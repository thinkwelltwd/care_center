from odoo import models, fields, api, _


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    medium_id = fields.Many2one('utm.medium', 'Medium',
                                help="This is the method of delivery. Ex: Email / Phonecall / API / Website")

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override to set message body to be in the
        Issue Description rather than first Chatter message
        """
        custom_values = dict(custom_values or {})
        if 'medium_id' not in custom_values and 'medium_id' not in msg:
            custom_values['medium_id'] = self.env.ref('utm.utm_medium_email').id
        if not msg.get('description', None):
            custom_values['description'] = msg.get('body', None)
        msg['body'] = None
        return super(ProjectIssue, self).message_new(msg, custom_values=custom_values)

    @api.multi
    def message_update(self, msg, update_vals=None):
        """Override to re-open issue if it was closed."""
        if not self.active:
            update_vals['active'] = True
        return super(ProjectIssue, self).message_update(msg, update_vals=update_vals)


    @api.multi
    def redirect_issue_view(self):
        """Enable redirecting to an issue when created from a phone call."""
        self.ensure_one()

        form_view = self.env.ref('project_issue.project_issue_form_view')
        tree_view = self.env.ref('project_issue.project_issue_tree_view')
        kanban_view = self.env.ref('project_issue.project_issue_view_kanban_inherit_no_group_create')
        calendar_view = self.env.ref('project_issue.project_issue_calendar_view')
        graph_view = self.env.ref('project_issue.project_issue_graph_view')

        return {
            'name': _('Issue'),
            'view_type': 'form',
            'view_mode': 'tree, form, calendar, kanban',
            'res_model': 'project.issue',
            'res_id': self.id,
            'view_id': False,
            'views': [
                (form_view.id, 'form'),
                (tree_view.id, 'tree'),
                (kanban_view.id, 'kanban'),
                (calendar_view.id, 'calendar'),
                (graph_view.id, 'graph')
            ],
            'type': 'ir.actions.act_window',
        }
