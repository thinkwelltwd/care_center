from odoo import models, fields, api, _


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    medium_id = fields.Many2one('utm.medium', 'Medium',
                                help="This is the method of delivery. Ex: Email / Phonecall / API / Website")
    description = fields.Html('Private Note')

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

    @api.model
    def api_message_new(self, msg):
        """
        Create an Issue via API call. Should be callable with the same signature as
        python's sending emails.

        @param dict msg: dictionary of message variables 
       :rtype: int
       :return: the id of the new Issue
        """

        Tag = self.env['project.tags']
        Project = self.env['project.project']
        project = msg.get('project', None) and Project.search([('name', '=', msg['project'])])

        data = {
            'project_id': project and project.id,
            'medium_id': self.env.ref('care_center.utm_medium_api').id,
            'tag_ids': [(6, False, [tag.id for tag in Tag.search([('name', 'in', msg.get('tags', []))])])],
        }

        if 'partner_id' not in msg and project and project.partner_id:
            data['partner_id'] = project.partner_id.id
            data['email_from'] = project.partner_id.email

        # Python's CC email param takes a list, so cast to string if necessary
        if isinstance(msg.get('cc', ''), (list, tuple)):
            msg['cc'] = ','.join(msg['cc'])

        msg.update(data)

        return super(ProjectIssue, self).message_new(msg, custom_values=data)

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

    @api.onchange('project_id')
    def _default_settings(self):

        if self.env.context.get('project_id', None):
            project = self.env['project.project'].browse(self.env.context['project_id'])
        else:
            project = self.project_id

        contract = project.analytic_account_id
        self.project_id = project.id
        self.partner_id = project.partner_id
        if contract.contact_id:
            self.email_from = contract.contact_id.email
        else:
            self.email_from = project.partner_id.email

        if self.env.context.get('project_tag', None):
            if not self.tag_ids:
                self.tag_ids = self.env['project.tags'].search([('name', '=', self.env.context['project_tag'])])

    def email_the_customer(self):
        """
        Helper function to be called from close_issue or email_customer.
        Can't be a decorated and be called from other dectorated methods
        """

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        template = self.env['mail.template'].search([('name', '=', 'CF Issue Reply')])
        ctx = {
            'default_model': 'project.issue',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'mass_mail',
        }
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def claim_issue(self):
        self.ensure_one()
        self.user_id = self._uid

    @api.multi
    def close_issue(self):
        self.ensure_one()
        self.stage_id = self.env['project.task.type'].search([('name', '=', 'Done')])
        self.active = False
        return self.email_the_customer()

    @api.multi
    def reopen_issue(self):
        self.ensure_one()
        self.stage_id = self.env['project.task.type'].search([('name', '=', 'Troubleshooting')])
        self.active = True

    @api.multi
    def email_customer(self):
        """
        Open a window to compose an email
        """
        self.ensure_one()
        return self.email_the_customer()
