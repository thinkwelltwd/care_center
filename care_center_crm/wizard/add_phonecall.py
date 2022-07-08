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

    @api.onchange('task_id')
    def set_phonecall_domain(self):
        domain = [
            ('opportunity_id', '=', False),
            ('task_id', '=', False),
        ]
        if self.task_id:
            partner_ids = self.get_partner_ids(field=self.task_id.partner_id)
            domain.append(('partner_id', 'in', partner_ids))

        return {
            'domain': {
                'phonecall_id': domain,
            },
        }

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

    @api.onchange('lead_id')
    def set_phonecall_domain(self):
        domain = [
            ('opportunity_id', '=', False),
            ('task_id', '=', False),
        ]
        if self.lead_id:
            partner_ids = self.get_partner_ids(field=self.lead_id.partner_id)
            domain.append(('partner_id', 'in', partner_ids))

        return {
            'domain': {
                'phonecall_id': domain,
            },
        }

    def set_lead_on_phonecall(self):
        self.phonecall_id.opportunity_id = self.lead_id.id
