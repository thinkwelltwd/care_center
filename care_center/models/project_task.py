from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Care Center Project Task'
    _inherit = ['care_center.base', 'project.task']

    parent_task_id = fields.Many2one(
        'project.task',
        string='Parent Task',
        ondelete='cascade',
        required=False,
    )
    child_task_ids = fields.One2many(
        'project.task',
        'parent_task_id',
        string='Sub Tasks',
    )
    medium_id = fields.Many2one(
        'utm.medium',
        'Medium',
        help="This is the method of delivery. "
             "Ex: Email / Phonecall / API / Website",
    )
    description = fields.Html('Private Note')
    task_active = fields.Boolean(compute='_task_active')
    subtask_count = fields.Integer(compute='_subtask_count')

    @api.model_create_multi
    def create(self, vals_list):

        # Reset user_id if task is created via email or API.
        # In those cases, such tasks should be unassigned.
        for values in vals_list:
            if 'medium_id' in values:
                medium = self.env['utm.medium'].search([
                    ('id', '=', values['medium_id']),
                ]).mapped('name')
                if medium and medium[0] in ('Email', 'API'):
                    values['user_id'] = False

        return super(ProjectTask, self).create(vals_list)

    @api.multi
    def _subtask_count(self):
        for task in self:
            task.subtask_count = len(task.child_task_ids)

    @api.multi
    def _task_active(self):
        for task in self:
            if not task.active:
                task.task_active = False
            elif task.stage_id.fold:
                task.task_active = False
            else:
                task.task_active = True

    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' \
                    and partner.parent_id \
                    and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                'title': title,
                'message': message,
            }
            if partner.sale_warn == 'block':
                self.update({
                    'partner_id': False,
                    'project_id': False,
                    'sale_line_id': False,
                })

        if warning:
            return {'warning': warning}

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override to set message body to be in the
        Ticket Description rather than first Chatter message
        """
        custom_values = dict(custom_values or {})
        if 'medium_id' not in custom_values and 'medium_id' not in msg:
            custom_values['medium_id'] = self.env.ref('utm.utm_medium_email').id
        if not msg.get('description', None):
            custom_values['description'] = msg.get('body', None)
        msg['body'] = None
        task = super(ProjectTask, self).message_new(msg, custom_values=custom_values)

        # Task company_id should match Partner's company_id!
        if task.partner_id and task.partner_id != task.company_id:
            task.write({'company_id': task.partner_id.company_id.id})

        return task

    @api.multi
    def message_update(self, msg, update_vals=None):
        """
        Override to re-open task if it was closed.
        Set stage to Customer Replied if current
        stage is folded or Waiting on Customer
        """
        update_vals = dict(update_vals or {})
        if not self.active:
            update_vals['active'] = True

        Stage = self.env['project.task.type']
        waiting_stage = Stage.search([
            ('name', '=', 'Waiting on Customer'),
        ], limit=1).mapped('id')

        if self.stage_id.fold or waiting_stage and self.stage_id.id == waiting_stage[0]:
            replied_stage = Stage.search([
                ('name', '=', 'Customer Replied'),
            ], limit=1).mapped('id')
            if replied_stage:
                update_vals['stage_id'] = replied_stage[0]

        return super(ProjectTask, self).message_update(msg, update_vals=update_vals)

    @api.model
    def api_message_new(self, msg):
        """
        Create a Ticket via API call. Should be callable with the same signature as
        python's sending emails.

        @param dict msg: dictionary of message variables 
       :rtype: int
       :return: the id of the new Ticket
        """

        Tag = self.env['project.tags']
        Project = self.env['project.project']
        project = msg.get('project', None) and Project.search([('name', '=', msg['project'])])
        tag_ids = Tag.search([('name', 'in', msg.get('tags', []))]).mapped('id')

        data = {
            'project_id': project and project.id,
            'medium_id': self.env.ref('care_center.utm_medium_api').id,
            'tag_ids': [(6, False, tag_ids)],
        }

        if 'partner_id' not in msg and project and project.partner_id:
            data['partner_id'] = project.partner_id.id
            data['email_from'] = project.partner_id.email

        # Python's CC email param takes a list, so cast to string if necessary
        if isinstance(msg.get('cc', ''), (list, tuple)):
            msg['cc'] = ','.join(msg['cc'])

        msg.update(data)

        return super(ProjectTask, self).message_new(msg, custom_values=data)

    @api.onchange('partner_id')
    def _partner_id(self):
        """
        Filter Tickets by Partner, including all
        Tickets of Partner Parent or Children
        """
        partner = self.partner_id

        if not partner:
            domain = []

        else:

            partner_ids = self.get_partner_ids()
            domain = self.get_partner_domain(partner_ids)

            # Only reset project if the Partner is set, and is
            # NOT related to the current Contact selected
            proj_partner = self.project_id.partner_id and self.project_id.partner_id.id
            if proj_partner and proj_partner not in partner_ids:
                self.project_id = None

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
                self.tag_ids = self.env['project.tags'].search([
                    ('name', '=', self.env.context['project_tag']),
                ])

    @api.constrains('project_id', 'partner_id')
    def check_matching_company(self):
        if not self.project_id or not self.partner_id or self.mailserver_mode():
            return

        proj_comp = self.project_id.company_id
        part_comp = self.partner_id.company_id

        if part_comp != proj_comp:
            msg = 'Project "{project_name}-{project_id}" company "{proj_comp_id}" does ' \
                  'not match Partner "{partner}-{partner_id}" company "{part_comp_id}".'.format(
                project_id=self.project_id.id,
                project_name=self.project_id.name,
                partner=self.partner_id.name,
                partner_id=self.partner_id.id,
                # .id because website error message mangles message string if using .name :(
                proj_comp_id=proj_comp.id,
                part_comp_id=part_comp.id,
            )
            # TODO in Odoo 13+, raise RedirectWarning and pass in an action + context for Project
            raise ValidationError(msg)

    def confirm_relationships(self):
        """
        If project has partner assigned, it must
        be related to the Ticket Partner.

        Call before closing to allow placeholder
        projects to be used until specific
        projects can be assigned.
        """
        invoiceable_timesheets = self.timesheet_ids.filtered(
            lambda ts: not ts.exclude_from_sale_order
        )

        if not self.project_id or not self.partner_id or not invoiceable_timesheets:
            return

        task_partner = self.partner_id.commercial_partner_id.id
        related_project_partners = self.project_id.related_partner_ids()

        if task_partner not in related_project_partners:
            task_partner = self.partner_id.name
            project_partner = self.project_id.partner_id.name or 'No Partner assigned to Project'
            raise ValidationError(
                'Task has invoiceable timesheets but Task Partner is not related to or associated '
                'with Project Partner.\n\n'
                'Project Partner: %s\n'
                'Task Partner: %s\n\n'
                'For correct billing, assign a Project associated with %s to this Task.' %
                (project_partner, task_partner, task_partner)
            )

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project. """
        tasks = self.browse(res_ids)
        project_ids = set(tasks.mapped('project_id').ids)
        aliases = self.env['project.project'].message_get_reply_to(
            list(project_ids),
            default=default,
        )
        return dict((task.id, aliases.get(task.project_id and task.project_id.id or 0, False))
                    for task in tasks)

    @api.multi
    def confirm_subtasks_done(self):
        for subtask in self.child_task_ids:
            if not subtask.active or subtask.stage_id.fold:
                continue

            raise ValidationError('Please close all open Sub Tasks')

    @api.model
    def _check_stage_id(self, stage_id):
        """
        Don't set stage to folded state unless all subtasks are Done.
        Archive task when stage is folded.
        """
        stage = self.env['project.task.type'].browse(stage_id)
        if stage and stage.fold:
            if self.child_task_ids:
                self.confirm_subtasks_done()
            self.toggle_active()

    @api.multi
    def write(self, values):
        """ on_change doesn't fire for stage_id clicks """
        if values.get('stage_id') and self.mailserver_mode():
            self._check_stage_id(values['stage_id'])
        return super(ProjectTask, self).write(values)

    @api.multi
    def close_task(self):
        self.ensure_one()
        self.confirm_subtasks_done()
        self.confirm_relationships()
        self.stage_id = self.env['project.task.type'].search([('name', '=', 'Done')])
        if self.active:
            self.toggle_active()

    @api.multi
    def reopen_ticket(self):
        self.ensure_one()
        self.stage_id = self.env['project.task.type'].search([('name', '=', 'In Progress')])
        self.active = True
        self.date_close = None

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """

        for record in self:
            if record.active:
                self.confirm_subtasks_done()
                self.date_close = fields.Datetime.now()
            else:
                self.date_close = None

        super(ProjectTask, self).toggle_active()

    @api.multi
    def open_subtasks(self):
        self.ensure_one()
        form = self.env.ref('care_center.project_task_required_fields', False)
        tree = self.env.ref('care_center.care_center_task_tree', False)

        parent_task_id = self.parent_task_id and self.parent_task_id.id or self.id
        context = {
            'default_partner_id': self.partner_id.id,
            'default_parent_task_id': parent_task_id,
            'default_project_id': self.project_id and self.project_id.id,
        }

        return {
            'name': 'Subtasks',
            'view_mode': 'tree,form',
            'views': [(tree.id, 'tree'), (form.id, 'form')],
            'view_id': tree.id,
            'res_model': 'project.task',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': False,
            'domain': [('parent_task_id', '=', parent_task_id)],
        }


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    _sql_constraints = [
        (
            'task_type_name_unique',
            'unique(name)',
            'There is already a task stage with that name!',
        ),
    ]
