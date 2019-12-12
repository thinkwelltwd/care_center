from odoo import api, fields, models
from odoo.exceptions import UserError


class AddInternalPhonecall(models.TransientModel):
    _name = 'add_internal_phonecall.wizard'
    _description = 'Create new internal phone call'

    def _get_task_id(self):
        return self.env['project.task'].browse(self.env.context.get('active_id'))

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        default=lambda self: self.env.context.get('active_id'),
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Callee',
        required=True,
        domain=[
            ('employee', '=', True),
        ],
    )

    @api.constrains('partner_id')
    def _check_partner_id(self):
        if self.env.uid == self.partner_id.get_odoo_user().id:
            raise UserError(f'You should not call yourself!')

    @api.multi
    def place_internal_phonecall(self):
        """
        Create phone call and pause callee's current active timesheet
        """
        Phonecall = self.env['crm.phonecall'].sudo()
        caller = self.env.uid

        vals = {
            'name': 'Internal Phonecall',
            'state': 'open',
            'task_id': self.task_id.id,
            'user_id': caller,
            'partner_id': self.partner_id.id,
            'project_id': self.task_id.project_id.id,
            'team_id': self.task_id.team_id and self.task_id.team_id.id,
            'source_id': self.env.ref('care_center_internal_crm.internal_company_calls').id,
        }

        phonecall = Phonecall.create(vals)
        self._handle_caller_timesheet(phonecall)
        self._handle_callee_timesheet(phonecall)

    def _handle_caller_timesheet(self, phonecall):
        """
        Associate caller's existing timesheet with phone call
        """
        caller = self.env.uid
        timesheet = self.task_id.sudo().timesheet_ids.filtered(
            lambda ts: ts.user_id.id == caller and ts.timer_status == 'running'
        )
        timesheet.sudo().write({'phonecall_id': phonecall.id})
        return timesheet

    def _handle_callee_timesheet(self, phonecall):
        """
        Associate callee's existing timesheet with phone call if
        current active timesheet so happens to be on this task.

        Otherwise, pause current timesheet and create new one.
        """
        callee_user_id = self.partner_id.get_odoo_user()

        callee_active_ts = callee_user_id.sudo().get_active_timesheet()
        if callee_active_ts:
            if callee_active_ts.task_id == self.task_id:
                callee_active_ts.write({'phonecall_id': phonecall.id})
                return callee_active_ts
            else:
                callee_active_ts.task_id.sudo().with_context(
                    user_id=callee_user_id.id,
                ).timer_pause()

        timesheet = self.task_id.sudo().with_context(user_id=callee_user_id.id).timer_start()
        timesheet.sudo().write({
            'phonecall_id': phonecall.id,
            'code': 'phone',
        })

        return timesheet
