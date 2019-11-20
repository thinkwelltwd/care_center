from odoo import models, fields


class TaskAssignment(models.Model):
    _name = 'task.assignment'
    _description = 'Care Center Task Assignment'

    name = fields.Char(
        'Summary',
        required=True,
        help='Short explanation for reassigning the Task.',
    )
    description = fields.Html(
        'Description',
        required=False,
        help='Extended explanation for reassigning the Task.',
    )
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        index=True,
        ondelete='cascade',
        required=False,
    )
    assigned_by = fields.Many2one(
        'res.users',
        string='Assigned By',
        index=True,
        ondelete='set null',
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        index=True,
        ondelete='set null',
    )
    team_id = fields.Many2one(
        'crm.team',
        string='Team',
        index=True,
        ondelete='set null',
        domain=[
            ('type_team', '!=', 'sales'),
        ],
        help='New Team responsible for performing this Task',
    )
