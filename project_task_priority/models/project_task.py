from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    priority = fields.Selection(
        selection_add=[
            ("2", "High"),
            ("3", "Urgent"),
            ("4", "Crisis"),
            ("5", "Disaster"),
        ]
    )
