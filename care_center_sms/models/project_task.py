from odoo import api, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def get_mobile_number(self):
        if not self.partner_id:
            return False
        return self.partner_id.mobile

    def sms_action(self):
        self.ensure_one()

        default_mobile = self.env['sms.number'].search([])[0]

        return {
            'name': 'SMS Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sms.compose',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_from_mobile_id': default_mobile.id,
                'default_to_number': self.get_mobile_number(),
                'default_record_id': self.id,
                'default_model': 'project.task',
            }
        }
