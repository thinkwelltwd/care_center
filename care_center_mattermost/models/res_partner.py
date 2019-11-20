from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mm_accesstoken = fields.Char(
        'Access Token',
        help='Mattermost Personal Access Token. '
        'Can be used when Mattermost '
        'authenticates against a Gitlab server',
    )
