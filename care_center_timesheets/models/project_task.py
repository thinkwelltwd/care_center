# -*- coding: utf-8 -*-
from odoo import models, api


class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['project.utils', 'project.task']

    @api.multi
    def write(self, vals):
        issue = super(ProjectTask, self).write(vals)

        if vals.get('partner_id') or vals.get('project_id'):
            self._update_timesheets()

        return issue
