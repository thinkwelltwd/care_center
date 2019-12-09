from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
valid_email = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class ExtraContactInfo(models.Model):
    _name = 'extra.contactinfo'
    _description = 'Extra Contact Info'
    _order = 'sequence asc'
    _sql_constraints = [
        (
            'extra_phone_email_unique',
            'unique(name)',
            'Extra Phone or Email records must be unique!',
        ),
    ]

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
    sequence = fields.Integer(
        default=1,
    )

    @api.constrains('name', 'type')
    def _validate_email_address(self):
        if self.type == 'email' and not valid_email.match(self.name):
            raise ValidationError(
                '{} is not a correctly formatted email address'.format(self.name)
            )

    @api.model
    def create(self, vals):
        if 'partner_id' in vals and vals.get('sequence', 1) == 1:
            vals['sequence'] = self.env['extra.contactinfo'].search_count([
                ('partner_id', '=', vals['partner_id']),
            ]) + 1
        return super().create(vals)
