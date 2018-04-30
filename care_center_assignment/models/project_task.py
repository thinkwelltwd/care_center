from odoo import api, models, fields


class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['care_center.base', 'project.task']

    assignment_ids = fields.One2many('task.assignment', 'task_id',
                                     string='Assignment History',
                                     ondelete='cascade', required=False)

    assignment_count = fields.Integer(compute='_assignment_count')

    @api.multi
    def _assignment_count(self):
        for task in self:
            task.assignment_count = len(task.assignment_ids)
