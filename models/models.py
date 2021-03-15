# -*- coding: utf-8 -*-
from odoo import fields, models ,api ,exceptions


class Course(models.Model):
    _name = 'oa.course'
    _description = 'Course OA'

    name = fields.Char(string='Title', required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users', string="Responsible", help="Need not be the Instructor")
    session_ids = fields.One2many('oa.session', 'course_id', string="Sessions")

    level = fields.Selection([('1', 'Easy'), ('2', 'Medium'), ('3', 'Hard')], string="Difficulty Level")
    session_count = fields.Integer(compute="_compute_session_count")


    @api.depends('session_ids')
    def _compute_session_count(self):
        for course in self:
            course.session_count = len(course.session_ids)


    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]

class Session(models.Model):
    _name = 'oa.session'
    _description = 'Session OA'

    name = fields.Char(required=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', "Draft"), ('confirmed', "Confirmed"), ('done', "Done")], default='draft')
    level = fields.Selection(related='course_id.level', readonly=True)
    responsible_id = fields.Many2one(related='course_id.responsible_id', readonly=True, store=True)


    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date(default=fields.Date.today)

    duration = fields.Float(digits=(6, 2), help="Duration in days", default=1)

    instructor_id = fields.Many2one('res.partner', string="Instructor")
    course_id = fields.Many2one('oa.course', ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    attendees_count = fields.Integer(compute='_get_attendees_count', store=True)


    seats = fields.Integer()

    ###
    ## Using computed fields
    ###
    taken_seats = fields.Float(compute='_compute_taken_seats', store=True)

    @api.depends('seats', 'attendee_ids')
    def _compute_taken_seats(self):
        for session in self:
            if not session.seats:
                session.taken_seats = 0.0
            else:
                session.taken_seats = 100.0 * len(session.attendee_ids) / session.seats


    ###
    ## using onchange
    ###
    @api.onchange('seats', 'attendee_ids')
    def _change_taken_seats(self):
        if self.taken_seats > 100:
            return {'warning': {
                'title':   'Too many attendees',
                'message': 'The room has %s available seats and there is %s attendees registered' % (self.seats, len(self.attendee_ids))
            }}

    ###
    ## using python constrains
    ###
    @api.constrains('seats', 'attendee_ids')
    def _check_taken_seats(self):
        for session in self:
            if session.taken_seats > 100:
                raise exceptions.ValidationError('The room capacity is  %s seats and there already %s attendees registered' % (session.seats, len(session.attendee_ids)))


    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for session in self:
            session.attendees_count = len(session.attendee_ids)

    @api.onchange('start_date', 'end_date')
    def _compute_duration(self):
        if not (self.start_date and self.end_date):
            return
        if self.end_date < self.start_date:
            return {'warning': {
                'title':   "Incorrect date value",
                'message': "End date is earlier then start date",
            }}
        delta = fields.Date.from_string(self.end_date) - fields.Date.from_string(self.start_date)
        self.duration = delta.days + 1


    ###
    ## using SQL constrains
    ###
    _sql_constraints = [
        # possible only if taken_seats is stored
        ('session_full', 'CHECK(taken_seats <= 100)', 'The room is full'),
    ]
