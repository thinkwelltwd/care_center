from lchttp import json_dumps

from odoo import api, fields, models


class SetTaskOnPhoneCallWizard(models.TransientModel):
    _name = 'set_task_on_phone.wizard'
    _inherit = 'care_center.base'
    _description = 'Set Task on Phone Call'

    def _get_task_id(self):
        return self.env['project.task'].browse(self.env.context.get('active_id'))

    task_id = fields.Many2one('project.task', string='Task', default=_get_task_id)
    phonecall_id = fields.Many2one('crm.phonecall', string='Phone call')
    phonecall_id_domain = fields.Char(
        compute='_compute_phonecall_id_domain',
        readonly=True,
        store=False,
    )

    @api.multi
    @api.depends('task_id')
    def _compute_phonecall_id_domain(self):
        for rec in self:
            domain = [
                ('opportunity_id', '=', False),
                ('task_id', '=', False),
            ]
            if rec.task_id:
                partner_ids = rec.get_partner_ids(field=rec.task_id.partner_id)
                domain.append(('partner_id', 'in', partner_ids))

            rec.phonecall_id_domain = json_dumps(domain)

    @api.multi
    def set_task_on_phonecall(self):
        """
        'write' method wants to return a view so, we use custom function
        so that we can just go back to current Ticket/Task page
        """
        self.phonecall_id.write({'task_id': self.task_id.id})
        return True


class SetLeadOnPhoneCallWizard(models.TransientModel):
    _name = 'set_lead_on_phone.wizard'
    _inherit = 'care_center.base'
    _description = 'Set Lead on Phone Call'

    def _get_lead_id(self):
        return self.env['crm.lead'].browse(self.env.context.get('active_id'))

    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', default=_get_lead_id)
    phonecall_id = fields.Many2one('crm.phonecall', string='Phone call')
    phonecall_id_domain = fields.Char(
        compute='_compute_phonecall_id_domain',
        readonly=True,
        store=False,
    )

    @api.multi
    @api.depends('lead_id')
    def _compute_phonecall_id_domain(self):
        for rec in self:
            domain = [
                ('opportunity_id', '=', False),
                ('task_id', '=', False),
            ]
            if rec.lead_id:
                partner_ids = rec.get_partner_ids(field=self.lead_id.partner_id)
                domain.append(('partner_id', 'in', partner_ids))
            rec.phonecall_id_domain = json_dumps(domain)

    @api.multi
    def set_lead_on_phonecall(self):
        """
        'write' method wants to return a view so, we use custom function
        so that we can just go back to current Ticket/Task page
        """
        self.phonecall_id.write({'opportunity_id': self.lead_id.id})
        return True
