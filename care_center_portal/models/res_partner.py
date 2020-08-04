from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def get_projects(self):
        self.ensure_one()

        Project = self.env['project.project']
        return Project.search([
            '|',
            ('partner_id', '=', self.id),
            ('partner_id', '=', self.commercial_partner_id.id),
        ])
