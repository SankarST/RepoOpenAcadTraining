# -*- coding: utf-8 -*-, api
from odoo import fields, models


class Partner(models.Model):
     _inherit = 'res.partner'
#    _name = 'oa.partner'
#    _description = 'Partner OA'


#     name = fields.Char()

     instructor = fields.Boolean(default=False)
     session_ids = fields.Many2many('oa.session', string="Attended Sessions", readonly=True)
