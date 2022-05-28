from odoo import _, api, fields, models
from odoo.fields import DATE_LENGTH
from odoo.exceptions import UserError


class CrmPhonecall(models.Model):
    _name = 'crm.phonecall'
    _inherit = ['care_center.base', 'crm.phonecall']

    def _available_task_lead_ids(self):
        """
        Enable dynamic domain filters when Editing
        records where the on_change doesn't fire
        """
        domain = [
            '|',
            ('partner_id', '=', False),
            ('partner_id', 'in', self.get_partner_ids()),
        ]
        self.available_task_ids = self.env['project.task'].search(domain)
        self.available_lead_ids = self.env['crm.lead'].search(domain)

    def _available_project_ids(self):
        """
        Enable dynamic domain filters when Editing
        records where the on_change doesn't fire
        """
        self.available_project_ids = self.env['project.project'].search([
            '|',
            ('catchall', '=', True),
            ('partner_id', 'in', self.get_partner_ids()),
        ])

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        index=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        index=True,
    )
    timesheet_ids = fields.One2many(
        comodel_name='account.analytic.line',
        inverse_name='phonecall_id',
    )

    # Compute these properties so they can serve as domains in xml views
    # active even on Edit mode when partner_id field hasn't been changed
    available_task_ids = fields.Many2many('project.task', compute='_available_task_lead_ids')
    available_lead_ids = fields.Many2many('crm.lead', compute='_available_task_lead_ids')
    available_project_ids = fields.Many2many('project.project', compute='_available_project_ids')

    description = fields.Html('Description')

    @api.onchange('partner_id')
    def _update_partner_id_domain(self):
        """
        Filter Tasks by Partner, including all
        Tasks of Partner Parent or Children
        """
        partner = self.partner_id
        task = self.task_id
        opportunity = self.opportunity_id
        project = self.project_id

        if not partner:
            return {
                'domain': {
                    'task_id': [],
                    'opportunity_id': [],
                    'project_id': [],
                }
            }

        partner_ids = self.get_partner_ids()
        domain = self.get_partner_domain(partner_ids)

        # Reset fields ONLY if the partner doesn't match! Otherwise, will always
        # clear partner_id field, due onchange methods on task_id / opportunity_id
        if task and task.partner_id and task.partner_id.id not in partner_ids:
            self.task_id = False
        if opportunity and opportunity.partner_id and opportunity.partner_id.id not in partner_ids:
            self.opportunity_id = False
        if project and not project.catchall and project.partner_id and project.partner_id.id not in partner_ids:
            self.project_id = False

        return {
            'domain': {
                'task_id': domain,
                'opportunity_id': domain,
                'project_id': [
                    '|',
                    ('catchall', '=', True),
                    ('partner_id', 'in', partner_ids),
                ],
            },
        }

    @api.onchange('task_id')
    def _set_details_from_task(self):
        """
        Set Team if possible. Search by name, to handle
        CRM & Support Teams which have different FKs
        """
        if not self.task_id:
            return
        if self.task_id.team_id:
            team = self.env['crm.team'].search([('name', '=', self.task_id.team_id.name)])
            self.team_id = team and team.id

        # Tasks with blank partners shouldn't erase self.partner_id!
        if self.task_id.partner_id and self.task_id.partner_id != self.partner_id:
            self.partner_id = self.task_id.partner_id.id

        if self.task_id.project_id:
            self.project_id = self.task_id.project_id.id

        if not self.tag_ids and self.task_id.tag_ids:
            tag_names = self.task_id.tag_ids.mapped('name')
            self.tag_ids = self.env['crm.tag'].search([('name', 'in', tag_names)])

    @api.onchange('opportunity_id')
    def _set_opportunity_team(self):
        if self.opportunity_id and self.opportunity_id.team_id:
            self.team_id = self.opportunity_id.team_id.id

    @api.model
    def _timesheet_prepare(self, vals):
        """
        Prepare timesheet values for writing timesheet from call duration.
        """
        if len(self) > 1:
            raise UserError('Assign timesheet values on one call at a time')
        date = vals.get('date', fields.Date.to_string(self.date))
        if not date:
            raise UserError(_('Date field must be filled.'))
        project_id = vals.get('project_id', self.project_id.id)
        task_id = vals.get('task_id', self.task_id.id)
        user_id = vals.get('user_id', self.user_id.id)
        unit_amount = vals.get('duration', self.duration)
        res = {
            'date': date[:DATE_LENGTH],
            'user_id': user_id,
            'name': vals.get('name', self.name),
            'project_id': project_id,
            'task_id': task_id,
            'unit_amount': unit_amount / 60.0,
            'code': 'phone',
        }
        return res

    @api.model
    def create(self, vals):
        add_timesheet = self.env.context.get('timesheet_from_call_duration', True)
        if add_timesheet and vals.get('project_id') and vals.get('duration', 0) > 0:
            timesheet_data = self._timesheet_prepare(vals)
            vals['timesheet_ids'] = vals.get('timesheet_ids', [])
            vals['timesheet_ids'].append((0, 0, timesheet_data))

        return super().create(vals)

    def write(self, vals):
        add_timesheet = self.env.context.get('timesheet_from_call_duration', True)
        if not add_timesheet:
            return super().write(vals)

        AccountAnalyticLine = self.env['account.analytic.line']
        for record in self:
            timesheet = AccountAnalyticLine.search([
                ('phonecall_id', '=', record.id),
                ('code', '=', 'phone'),
            ])
            project_id = vals.get('project_id', record.project_id.id)
            duration = vals.get('duration', record.duration) or 0
            can_create_ts = project_id and duration > 0
            if can_create_ts:
                vals.update({
                    'project_id': project_id,
                    'duration': duration,
                })
            if timesheet:
                if not can_create_ts:
                    vals['timesheet_ids'] = [(2, timesheet.id, 0)]
                else:
                    vals['timesheet_ids'] = [(1, timesheet.id, self._timesheet_prepare(vals))]
            elif can_create_ts:
                vals['timesheet_ids'] = [(0, 0, self._timesheet_prepare(vals))]

        return super().write(vals)

    def button_end_call(self):
        end_date = fields.Datetime.now()
        for call in self:
            if call.date:
                start_date = fields.Datetime.from_string(call.date)
                if end_date < start_date:
                    call.duration = 0
                else:
                    call.duration = (end_date - start_date).total_seconds() / 60.0
        return True
