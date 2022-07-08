from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_projects(self):
        self.ensure_one()

        return self.partner_id.get_projects()
