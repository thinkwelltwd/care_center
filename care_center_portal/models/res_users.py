from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def get_projects(self):
        self.ensure_one()

        return self.partner_id.get_projects()
