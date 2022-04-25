from odoo import api, models, fields


class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Care Center Assignment Project Task'
    _inherit = ['care_center.base', 'project.task']

    assignment_ids = fields.One2many(
        'task.assignment',
        'task_id',
        string='Assignment History',
        ondelete='cascade',
        required=False,
    )

    assignment_count = fields.Integer(compute='_assignment_count')
    assignment_message = fields.Char(
        compute='_assignment_message',
        help='Assignment description to include in email templates.',
    )

    def _assignment_count(self):
        for task in self:
            task.assignment_count = len(task.assignment_ids)

    def _assignment_message(self):
        for task in self:
            if task.user_id:
                uname = task.user_id.name
                if not task.team_id:
                    task.assignment_message = "%s's queue" % uname
                else:
                    task.assignment_message = "%s from the %s team" % (uname, task.team_id.name)
            elif task.team_id:
                task.assignment_message = 'the %s team' % task.team_id.name
            else:
                task.assignment_message = 'the general queue'
