from odoo import api, fields, models


class CrmPhonecall2phonecall(models.TransientModel):
    _inherit = 'crm.phonecall2phonecall'

    def _get_task_id(self):
        return self.env['crm.phonecall'].browse(
            self.env.context.get('active_id')
        ).task_id.id

    def _get_project_id(self):
        return self.env['crm.phonecall'].browse(
            self.env.context.get('active_id')
        ).project_id.id

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        default=_get_task_id,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        default=_get_project_id,
        domain="[('partner_id', '=', partner_id)]",
    )

    def get_vals_action_schedule(self):
        vals = super().get_vals_action_schedule()
        vals.update({
            'task_id': self.task_id.id or False,
            'project_id': self.project_id.id or False,
            'direction': 'out',
        })
        return vals

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['date'] = fields.Datetime.now()
        return res
