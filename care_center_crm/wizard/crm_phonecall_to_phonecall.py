from odoo import api, fields, models


class CrmPhonecall2phonecall(models.TransientModel):
    _inherit = 'crm.phonecall2phonecall'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        index=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        index=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(CrmPhonecall2phonecall, self).default_get(fields)
        call = self.env['crm.phonecall'].browse(self.env.context.get('active_id'))
        if not call:
            return res

        if call.task_id:
            res['task_id'] = call.task_id.id

        if call.project_id:
            res['project_id'] = call.project_id.id

        return res
