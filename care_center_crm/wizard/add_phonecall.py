from lchttp import json_dumps

from odoo import api, fields, models


class SetTaskOnPhoneCallWizard(models.TransientModel):
    _name = 'set_task_on_phone.wizard'
    _inherit = 'care_center.base'
    _description = 'Set Task on Phone Call'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        default=lambda self: self.env.context.get('active_id'),
    )
    phonecall_id = fields.Many2one('crm.phonecall', string='Phone call')
    phonecall_id_domain = fields.Char(
        compute='_compute_phonecall_id_domain',
        readonly=True,
        store=False,
    )

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

    def set_task_on_phonecall(self):
        self.phonecall_id.task_id = self.task_id.id


class SetLeadOnPhoneCallWizard(models.TransientModel):
    _name = 'set_lead_on_phone.wizard'
    _inherit = 'care_center.base'
    _description = 'Set Lead on Phone Call'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead/Opportunity',
        default=lambda self: self.env.context.get('active_id'),
    )
    phonecall_id = fields.Many2one('crm.phonecall', string='Phone call')
    phonecall_id_domain = fields.Char(
        compute='_compute_phonecall_id_domain',
        readonly=True,
        store=False,
    )

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

    def set_lead_on_phonecall(self):
        self.phonecall_id.opportunity_id = self.lead_id.id
