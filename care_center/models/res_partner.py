from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_task_count(self):
        """
        Override compute method to count tasks assigned to company contacts as well
        """
        for partner in self:
            partner.task_count = self.env['project.task'].search_count([
                '|',
                ('partner_id', '=', partner.id),
                ('commercial_partner_id', '=', partner.id),
            ])
