import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError

valid_email = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class ExtraContactInfo(models.Model):
    _name = 'extra.contactinfo'
    _inherit = ['phone.validation.mixin']
    _description = 'Extra Contact Info'

    name = fields.Char(
        string='Phone/Email',
        required=True,
    )
    type = fields.Selection(
        selection=[
            ('phone', 'Phone'),
            ('mobile', 'Mobile'),
            ('email', 'Email'),
        ],
        string='Type',
        required=True,
    )
    notes = fields.Html(
        string='Notes',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True,
    )

    _sql_constraints = [
        (
            'extra_phone_email_unique',
            'unique(name)',
            'Extra Phone or Email records must be unique!',
        ),
    ]

    @api.constrains('name', 'type')
    def _validate_email_address(self):
        if self.type == 'email' and not valid_email.match(self.name):
            raise ValidationError(
                '{} is not a correctly formatted email address'.format(self.name)
            )

    @api.onchange('name')
    def _format_phone_number(self):
        if not self.type or not self.name or self.type == 'email':
            return
        self.name = self.phone_format(self.name)
