from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_service_provider = fields.Boolean(string='Is Service Provider', default=False)
