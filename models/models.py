# -*- coding: utf-8 -*-
import logging

from datetime import timedelta
from odoo import fields, models ,api ,exceptions

_logger = logging.getLogger(__name__)

class Course(models.Model):
#    _name = 'oa.course'
#    _description = 'Course OA'
#    _inherit = 'mail.thread'
    
    _inherit = 'product.template'
    name = fields.Char(string='Title', required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users', string="Responsible", help="Need not be the Instructor", index=True, store=True)
    can_edit_responsible = fields.Boolean(compute='_compute_can_edit_responsible')

    is_course = fields.Boolean(string="Is OA Course" , default = False)
    session_ids = fields.One2many('oa.session', 'course_id', string="Sessions")

    level = fields.Selection([('1', 'Easy'), ('2', 'Medium'), ('3', 'Hard')], string="Difficulty Level")
    session_count = fields.Integer(compute="_compute_session_count")
    attendee_count = fields.Integer(compute="_compute_attendee_count")
    color = fields.Integer()

    fname = fields.Char('Filename')
    datas = fields.Binary('File')
    currency_id = fields.Many2one('res.currency', 'Currency')

    price = fields.Float('Price', related='list_price')

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]



    @api.depends('responsible_id')
    def _compute_can_edit_responsible(self):
        self.can_edit_responsible = self.env.user.has_group('oa.group_archmaesters')


    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    def open_attendees(self):
        self.ensure_one()
        attendee_ids = self.session_ids.mapped('attendee_ids')
        return {
            'name':      'Attendees of %s' % (self.name),
            'type':      'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain':    [('id', 'in', attendee_ids.ids)],
        }

    @api.depends('session_ids')
    def _compute_session_count(self):
        for course in self:
            course.session_count = len(course.session_ids)

    @api.depends('session_ids.attendees_count')
    def _compute_attendee_count(self):
        for course in self:
            course.attendee_count = len(course.mapped('session_ids.attendee_ids'))


class Session(models.Model):
    _name = 'oa.session'
    _inherit = ['mail.thread']
    _order = 'name'
    _description = 'Session OA'
 
    name = fields.Char(required=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', "Draft"), ('confirmed', "Confirmed"), ('done', "Done")], default='draft')
    level = fields.Selection(related='course_id.level', readonly=True)
    responsible_id = fields.Many2one(related='course_id.responsible_id', readonly=True, store=True)


    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date(string='End Date', store=True, compute='_get_end_date', inverse='_set_end_date')
    duration = fields.Float(digits=(6, 2), help="Duration in days", default=1)

    instructor_id = fields.Many2one('res.partner', string="Instructor")
#    course_id = fields.Many2one('oa.course', ondelete='cascade', string="Course", required=True)
    course_id = fields.Many2one('product.template', ondelete='cascade', string="Course" ,required=True , domain=[('is_course','=',True)])

    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    attendees_count = fields.Integer(compute='_get_attendees_count', store=True)

    seats = fields.Integer()
    ## Using computed fields
    taken_seats = fields.Float(compute='_compute_taken_seats', store=True)
    percentage_per_day = fields.Integer("%", default=100)


    is_paid = fields.Boolean('Is paid')
#    product_id = fields.Many2one('product.template', 'Product')
                  


    def _warning(self, title, message):
        return {'warning': {
            'title':   title,
            'message': message,
        }}

    @api.depends('seats', 'attendee_ids')
    def _compute_taken_seats(self):
        for session in self:
            if not session.seats:
                session.taken_seats = 0.0
            else:
                session.taken_seats = 100.0 * len(session.attendee_ids) / session.seats

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for session in self:
            session.attendees_count = len(session.attendee_ids)

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return self._warning("Incorrect 'seats' value", "The number of available seats may not be negative")
        if self.seats < len(self.attendee_ids):
            return self._warning("Too many attendees", "Increase seats or remove excess attendees")


    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for session in self:
            if session.instructor_id and session.instructor_id in session.attendee_ids:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for session in self:
            if not (session.start_date and session.duration):
                session.end_date = session.start_date
            else:
                # Add duration to start_date, but: Monday + 5 days = Saturday,
                # so subtract one second to get on Friday instead
                start = fields.Datetime.from_string(session.start_date)
                duration = timedelta(days=session.duration, seconds=-1)
                session.end_date = str(start + duration)

    def _set_end_date(self):
        for session in self:
            if session.start_date and session.end_date:
                # Compute the difference between dates, but: Friday - Monday = 4
                # days, so add one day to get 5 days instead
                start_date = fields.Datetime.from_string(session.start_date)
                end_date = fields.Datetime.from_string(session.end_date)
                session.duration = (end_date - start_date).days + 1




    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.message_post(body="Session %s of the course %s reset to draft" % (rec.name, rec.course_id.name))

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            rec.message_post(body="Session %s of the course %s confirmed" % (rec.name, rec.course_id.name))

    def action_done(self):
        for rec in self:
            rec.state = 'done'
            rec.message_post(body="Session %s of the course %s done" % (rec.name, rec.course_id.name))

    def _auto_transition(self):
        for rec in self:
            if rec.taken_seats >= 50.0 and rec.state == 'draft':
                rec.action_confirm()

    def write(self, vals):
        res = super(Session, self).write(vals)
        for rec in self:
            rec._auto_transition()
        if vals.get('instructor_id'):
            self.message_subscribe([vals['instructor_id']])
        return res

    @api.model
    def create(self, vals):
        logging.warning('##---------- --------------- Test %s ' % str(self.course_id) )
        res = super(Session, self).create(vals)
        res._auto_transition()
        if vals.get('instructor_id'):
            res.message_subscribe([vals['instructor_id']])
        return res


    def create_invoice_teacher(self):


        logging.warning('##---------- Create Invoice Teacher %s ' % str(self.instructor_id.id) )

        teacher_invoice = self.env['account.move'].search([
            ('partner_id', '=', self.instructor_id.id)
        ], limit=1)



        if not teacher_invoice:
            teacher_invoice = self.env['account.move'].create({
                'partner_id': self.instructor_id.id,
            })

        logging.warning('##------------At line  3a %s '  % str(teacher_invoice.id) )

        # install module accounting and a chart of account to have at least one expense account in your CoA
        expense_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)], limit=1)

        logging.warning('##------------At line  4 %s '  % str(expense_account.id) )
#        logging.warning('##------------At line  5 %s '  % str(product_id.id) )
        product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=' ,self.course_id.id)] , limit=1)
        logging.warning('##------------At line  66 %s '  % str(product_id.id) )
        
        move_line = self.env['account.move.line'].create({
            'move_id': teacher_invoice.id,
            'product_id': product_id.id,
            'price_unit': product_id.lst_price,
            'account_id': expense_account.id,
            'name':       'Session',
            'quantity':   1,
#	    'debit' : self.course_id.lst_price ,	
#	    'credit' : self.course_id.lst_price	
        })

        logging.info('##--------------At line 67 %s '  , move_line) 

        self.write({'is_paid': True})


## done in get  , set end date
#    @api.onchange('start_date', 'end_date')
#    def _compute_duration(self):
#        if not (self.start_date and self.end_date):
#            return
#        if self.end_date < self.start_date:
#            return {'warning': {
#                'title':   "Incorrect date value",
#                'message': "End date is earlier then start date",
#            }}
#        delta = fields.Date.from_string(self.end_date) - fields.Date.from_string(self.start_date)
#        self.duration = delta.days + 1


    ###
    ## using SQL constrains
    ###
#    _sql_constraints = [
#        # possible only if taken_seats is stored
#        ('session_full', 'CHECK(taken_seats <= 100)', 'The room is full'),
#   ]


    ###
    ## using onchange
    ###
## done by _verify_valid_seats
#    @api.onchange('seats', 'attendee_ids')
#    def _change_taken_seats(self):
#        if self.taken_seats > 100:
#            return {'warning': {
#                'title':   'Too many attendees',
#                'message': 'The room has %s available seats and there is %s attendees registered' % (self.seats, len(self.attendee_ids))
#            }}

    ###
    ## using python constrains
    ###
## done by _verify_valid_seats
#    @api.constrains('seats', 'attendee_ids')
#    def _check_taken_seats(self):
#        for session in self:
#            if session.taken_seats > 100:
#                raise exceptions.ValidationError('The room capacity is  %s seats and there already %s attendees registered' % (session.seats, len(session.attendee_ids)))

