from odoo import models, fields, api, _


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override to set message body to be in the
        Issue Description rather than first Chatter message
        """
        custom_values = dict(custom_values or {})
        custom_values['description'] = msg.get('body', None)
        msg['body'] = None
        return super(ProjectIssue, self).message_new(msg, custom_values=custom_values)

    @api.multi
    def message_update(self, msg, update_vals=None):
        """Override to re-open issue if it was closed."""
        if not self.active:
            update_vals['active'] = True
        return super(ProjectIssue, self).message_update(msg, update_vals=update_vals)
