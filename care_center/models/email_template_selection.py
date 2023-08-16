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
    )
    tag_id = fields.Many2one(
        'project.tags',
        string='Tag',
        required=True,
        help='Template '
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

    _sql_constraints = [(
        'template_tag_type_unique',
        'UNIQUE(tag_id,reply_type)',
        'Template already assigned for this Tag and Reply Type',
    )]
