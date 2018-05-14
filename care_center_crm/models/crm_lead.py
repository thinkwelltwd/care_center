# -*- coding: utf-8 -*-
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
