from odoo import fields, models


class EmailTemplateSelection(models.Model):
    _name = 'email.template.selection'
    _description = 'Email template selections by tag.'

    name = fields.Char(related='template_id.name')

    template_id = fields.Many2one(
        'mail.template',
        string='Template',
        required=True,
        domain=[('model', '=', 'project.task')],
        help='Email template that will be auto-selected when Tag and Team fields match a Task',
    )
    tag_id = fields.Many2one(
        'project.tags',
        string='Tag',
        required=True,
        help='Template can be used on Tasks with this Tag',
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
        index=True,
        help='Template can be used on Tasks assigned to this Team',
        domain=[('type_team', '!=', 'sales')],
    )
    reply_type = fields.Selection(
        selection=[
            ('reply', 'Reply to Customer'),
            ('initial', 'Initial Reply to Customer'),
            ('close', 'Closing Ticket'),
        ],
        default='reply',
        required=True,
    )

    _sql_constraints = [
        (
            'template_tag_type_unique',
            'UNIQUE(tag_id,team_id,reply_type)',
            'Template already assigned for this Tag, Team and Reply Type',
        ),
    ]
