# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
        index=True,
        help='Team responsible for performing this Task'
    )

    @api.onchange('project_id')
    def _set_team_from_project(self):
        if self.project_id.team_id:
            self.team_id = self.project_id.team_id.id
