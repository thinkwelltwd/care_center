from odoo import fields, models

class EmailTemplateSelection(models.Model):
    _name = 'email.template.selection'
    _description = 'Email template selections by tag.'

    template_id = fields.Many2one(
        'mail.template',
        string='Device',
        required=True,
        domain=[('model', '=', 'project.task')],
    )
    tag_id = fields.Many2one(
        'project.tags',
        string='Tag',
        required=True,
    )
    reply_type = fields.Selection(
        selection=[
            ('reply', 'Reply'),
            ('close', 'Closing Ticket'),
        ],
    )

    _sql_constraints = [(
        'template_tag_type_unique',
        'UNIQUE(tag_id,reply_type)',
        'Template already assigned for this Tag and Reply Type',
    )]
