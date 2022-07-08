from odoo import models, fields
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Care Center CRM Project Task'
    _inherit = ['care_center.base', 'project.task']

    phonecall_ids = fields.One2many(
        comodel_name='crm.phonecall',
        inverse_name='task_id',
        string='Phonecalls',
    )
    phonecall_count = fields.Integer(
        compute='_phonecall_count',
        string="Phonecall Count",
    )
    convertable = fields.Boolean(compute='_can_be_converted')
    active_phonecall_id = fields.Many2one(
        'crm.phonecall',
        string='Active Phonecall',
        compute='_user_active_call',
    )

    def _user_active_call(self):
        for task in self:
            active_timesheets = task.timesheet_ids.filtered(
                lambda ts: ts.phonecall_id
                           and ts.phonecall_id.state == 'open'
                           and ts.user_id.id == self.env.uid
                           and ts.timer_status == 'running'
            )
            task.active_phonecall_id = active_timesheets and active_timesheets.phonecall_id.id or False

    def _can_be_converted(self):
        for task in self:
            task.convertable = task.active and not len(task.timesheet_ids) and not task.stage_id.fold

    def _phonecall_count(self):
        for task in self:
            task.phonecall_count = self.env['crm.phonecall'].search_count([
                ('task_id', '=', task.id),
            ])

    def get_tag_ids(self):
        """
        When converting Task to Opportunity, carry Tags over if name is exact match
        """
        if not self.tag_ids:
            return []
        tag_names = self.tag_ids.mapped('name')
        return self.env['crm.tag'].search([('name', 'in', tag_names)]).mapped('id')

    def get_team_id(self):
        """
        When converting Task to Opportunity, carry Team over,
        if Suffix is Support instead of Sales
        """
        if not self.team_id:
            return False
        name = self.team_id.name
        if name.lower().endswith('support'):
            name = name[:7].strip()
        team = self.env['crm.team'].search(
            [
                '|',
                ('name', '=', name),
                ('name', '=', '%s Sales' % name),
            ],
            limit=1,
        )
        return team and team.id

    def move_phonecalls(self, opportunity_id):
        task_calls = self.env['crm.phonecall'].search([
            ('task_id', '=', self.id),
        ])
        task_calls.task_id = False
        task_calls.opportunity_id = opportunity_id

    def move_attachments(self, opportunity_id):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'project.task'),
            ('res_id', '=', self.id),
        ])
        attachments.res_model = 'crm.lead'
        attachments.res_id = opportunity_id

    def convert_to_opportunity(self):
        """
        Tasks may get created prematurely, or from emails sent to the incorrect alias.
        Helper function to convert such Tasks to Opportunities.
        """
        self.ensure_one()
        if not self.partner_id:
            raise UserError('Please specify a Customer before converting to Opportunity.')

        if self.timesheet_ids:
            raise UserError('Cannot convert to Opportunity after Timesheets are assigned.')

        opportunity = self.env['crm.lead'].create({
            'name': self.name,
            'planned_revenue': 0.0,
            'probability': 0.0,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.get_team_id(),
            'description': self.description,
            'priority': self.priority,
            'type': 'opportunity',
            'phone': self.partner_id.phone,
            'email_from': self.partner_id.email,
            'medium_id': self.medium_id and self.medium_id.id,
            'tag_ids': [(6, 0, self.get_tag_ids())],
        })
        opportunity._onchange_partner_id()
        self.move_phonecalls(opportunity_id=opportunity.id)
        self.move_attachments(opportunity_id=opportunity.id)
        self.message_change_thread(opportunity)
        self.active = False

        return {
            'name': 'Convert Task to Opportunity',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm.crm_case_form_view_oppor').id,
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': opportunity.id,
        }

    def action_view_phonecalls(self):
        """
        Display Phonecalls associated with this task.
        If only one is found, display the record directly.

        Otherwise, display tree view.
        """
        self.ensure_one()

        call_id = self.phonecall_ids
        if self.active_phonecall_id:
            call_id = self.active_phonecall_id

        view = {
            'name': 'Task Logged Calls',
            'res_model': 'crm.phonecall',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree,calendar',
            'context': {
                'default_task_id': self.id,
                'search_default_task_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

        if len(call_id) == 1:
            view.update({
                'res_id': call_id.id,
            })
        else:

            view.update({
                'view_mode': 'tree,form,calendar',
            })

        return view
