from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    priority = fields.Selection(
        selection_add=[
            ("2", "High"),
            ("3", "Urgent"),
            ("4", "Crisis"),
            ("5", "Disaster"),
        ],
        ondelete={
            '2': lambda p: p.write({'priority': '1'}),
            '3': lambda p: p.write({'priority': '1'}),
            '4': lambda p: p.write({'priority': '1'}),
            '5': lambda p: p.write({'priority': '1'}),
        }
    )

    def toggle_active(self):
        """Reset priority when archiving task"""
        super(ProjectTask, self).toggle_active()

        for record in self:
            if record.active:
                self.priority = '0'
