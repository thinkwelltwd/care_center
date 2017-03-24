from odoo import models, fields, api, _


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    support_team_id = fields.Many2one(
        'support.team', 'Support Team',
        help='Team responsible for resolving this Issue'
    )

    @api.onchange('partner_id')
    def _set_support_team(self):
        if self.partner_id.support_team_id:
            self.support_team_id = self.partner_id.support_team_id.id
