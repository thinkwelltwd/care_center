from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    medium_id = fields.Many2one('utm.medium', 'Medium',
                                help="This is the method of delivery. "
                                     "Ex: Email / Phonecall / API / Website")
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
        update_vals = dict(update_vals or {})
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

    @api.onchange('partner_id')
    def _partner_id(self):
        """
        Filter Issues by Partner, including all
        Issues of Partner Parent or Children
        """
        partner = self.partner_id

        if not partner:
            return {
                'domain': {
                    'project_id': [],
                }
            }

        # Always get ALL issues related to the company,
        # whether the partner_id is Company or Contact
        partner_ids = {partner.id}
        parent_id = partner.parent_id and partner.parent_id.id or partner.id
        if parent_id:
            partner_ids.add(parent_id)
            partner_ids.update(
                    [rp.id for rp in self.env['res.partner'].search([('parent_id', '=', parent_id)])]
                )

        # Only reset project if the Partner is set, and is
        # NOT related to the current Contact selected
        proj_partner = self.project_id.partner_id and self.project_id.partner_id.id
        if proj_partner and proj_partner not in partner_ids:
            self.project_id = None

        domain = [
            '|',
            ('partner_id', '=', False),
            ('partner_id', 'in', list(partner_ids)),
        ]

        return {
            'domain': {
                'project_id': domain,
            },
        }

    @api.onchange('project_id')
    def _project_id(self):

        if not self.date_deadline:
            self.date_deadline = fields.Date.to_string(date.today() + timedelta(hours=48))

        if self.env.context.get('project_tag', None):
            if not self.tag_ids:
                self.tag_ids = self.env['project.tags'].search([('name', '=', self.env.context['project_tag'])])

    @api.constrains('project_id')
    def check_relationships(self):
        """
        If project has partner assigned, it must
        be related to the Issue Partner
        """
        proj_partner = self.project_id.partner_id.id
        if not proj_partner:
            return

        issue_partner = self.partner_id and self.partner_id.id
        issue_parent_partner = self.partner_id and \
                               self.partner_id.parent_id and \
                               self.partner_id.parent_id.id

        if proj_partner != issue_partner and proj_partner != issue_parent_partner:
            raise ValidationError(
                'Project Contact and Issue Contact must be the same, '
                'or have the same parent Company.'
            )

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project. """
        issues = self.browse(res_ids)
        project_ids = set(issues.mapped('project_id').ids)
        aliases = self.env['project.project'].message_get_reply_to(list(project_ids), default=default)
        return dict((issue.id, aliases.get(issue.project_id and issue.project_id.id or 0, False)) for issue in issues)

    def email_the_customer(self):
        """
        Helper function to be called from close_issue or email_customer.
        Can't be a decorated and be called from other dectorated methods
        """

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        template = self.env['mail.template'].search([('name', '=', 'CF Issue - Close')])
        ctx = {
            'default_model': 'project.issue',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
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
        if self.active:
            self.toggle_active()
        return self.email_the_customer()

    @api.multi
    def reopen_issue(self):
        self.ensure_one()
        self.stage_id = self.env['project.task.type'].search([('name', '=', 'Troubleshooting')])
        self.active = True
        self.date_close = None

    @api.multi
    def email_customer(self):
        """
        Open a window to compose an email
        """
        self.ensure_one()
        return self.email_the_customer()

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """

        for record in self:
            if record.active:
                self.date_close = fields.Datetime.now()
            else:
                self.date_close = None

        super(ProjectIssue, self).toggle_active()
