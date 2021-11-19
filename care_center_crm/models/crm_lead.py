from odoo import models, fields, api


class Lead(models.Model):
    _inherit = 'crm.lead'

    description = fields.Html('Notes')
    convertable = fields.Boolean(compute='_can_be_converted')

    @api.multi
    def _can_be_converted(self):
        for lead in self:
            convertable = True
            if not lead.active:
                convertable = False
            elif lead.stage_id.fold:
                convertable = False
            elif lead.probability == 100:
                convertable = False
            elif len(lead.order_ids):
                convertable = False
            lead.convertable = convertable

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override to set message body to be in the
        Description rather than first Chatter message
        """
        custom_values = dict(custom_values or {})
        if 'medium_id' not in custom_values and 'medium_id' not in msg:
            custom_values['medium_id'] = self.env.ref('utm.utm_medium_email').id
        if not msg.get('description', None):
            custom_values['description'] = msg.get('body', None)
        msg['body'] = None
        return super(Lead, self).message_new(msg, custom_values=custom_values)

    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        """
        Override to re-open lead if it was closed.
        Set stage to Customer Replied if current
        stage is folded or Waiting for response
        """
        update_vals = dict(update_vals or {})
        if not self.active:
            update_vals['active'] = True

        Stage = self.env['crm.stage']
        waiting_stage = Stage.search([
            ('name', '=', 'Waiting for response'),
        ], limit=1).mapped('id')

        if self.stage_id.fold or waiting_stage and self.stage_id.id == waiting_stage[0]:
            replied_stage = Stage.search([
                ('name', '=', 'Customer Replied'),
            ], limit=1).mapped('id')
            if replied_stage:
                update_vals['stage_id'] = replied_stage[0]

        return super(Lead, self).message_update(msg_dict, update_vals=update_vals)
