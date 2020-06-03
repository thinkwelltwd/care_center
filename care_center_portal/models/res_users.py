from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def get_projects(self):
        self.ensure_one()

        Project = self.env['project.project']
        return Project.search([
            '|',
            ('partner_id', '=', self.partner_id.id),
            ('partner_id', '=', self.partner_id.commercial_partner_id.id),
        ])
