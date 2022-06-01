from odoo import models, fields


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    contact_info_ids = fields.One2many(
        'extra.contactinfo',
        'partner_id',
        string='Extra Contact Info',
    )
