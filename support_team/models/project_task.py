from odoo import models, fields, api


class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['project.task', 'project.tag.team.base']

    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
        index=True,
        help='Team responsible for performing this Task',
        domain=[('type_team', '!=', 'sales')],
    )

    @api.onchange('project_id')
    def _set_team_from_project(self):
        project_team = self.project_id.team_id
        if self.project_id.team_id and project_team != self.team_id:
            self.team_id = self.project_id.team_id.id
