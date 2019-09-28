from odoo import api, fields, models


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

    @api.multi
    def toggle_active(self):
        """Reset priority when archiving task"""
        super(ProjectTask, self).toggle_active()

        for record in self:
            if record.active:
                self.priority = '0'
