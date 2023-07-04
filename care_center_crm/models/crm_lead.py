from markupsafe import Markup
from odoo import models, fields, api


class Lead(models.Model):
    _inherit = 'crm.lead'

    description = fields.Html('Notes')
    convertable = fields.Boolean(compute='_can_be_converted')

    def _can_be_converted(self):
        for lead in self:
            lead.convertable = lead.active and not lead.stage_id.fold and lead.probability != 100 and not len(lead.order_ids)

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

    def message_update(self, msg_dict, update_vals=None):
        """
        Override to re-open lead if it was closed
        and set stage to Customer Replied
        """
        update_vals = dict(update_vals or {})
        if not self.active:
            update_vals['active'] = True

        replied_stage = self.env['crm.stage'].search([
            ('name', '=', 'Customer Replied'),
        ], limit=1).mapped('id')
        if replied_stage:
            update_vals['stage_id'] = replied_stage[0]

        return super(Lead, self).message_update(msg_dict, update_vals=update_vals)

    def safe_description(self):
        """
        Wrap description in Markup object for unescaped display in Qweb templates.
        """
        return Markup(self.description)
