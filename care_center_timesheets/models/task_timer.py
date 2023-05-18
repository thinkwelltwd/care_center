from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..utils import get_factored_duration


class TaskDurationFields(models.AbstractModel):
    _name = 'task.duration.fields'
    _description = "Duration calculations for Timesheets"

    date_start = fields.Datetime('Started')
    factor = fields.Many2one(
        'hr_timesheet_invoice.factor',
        'Factor',
        default=lambda s: s.env['hr_timesheet_invoice.factor'].search(
            [('factor', '=', 0.0)],
            limit=1,
        ),
        help="Set the billing percentage when making invoice invoice.",
    )
    full_duration = fields.Float(
        string='Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet',
    )
    full_duration_rounded = fields.Float(compute='_round_full_duration')
    billable_time = fields.Float(compute='_get_billable_time')

    @api.depends('full_duration')
    def _round_full_duration(self):
        for rec in self:
            rec.full_duration_rounded = round(rec.full_duration, 2)

    @api.depends('full_duration_rounded')
    def _get_billable_time(self):
        for rec in self:
            factored_duration = get_factored_duration(
                hours=rec.full_duration_rounded,
                invoice_factor=rec.factor,
            )
            rec.billable_time = round(factored_duration, 2)


class TaskTimer(models.AbstractModel):
    _name = 'task.timer'
    _description = "Utils for Tasks / Tickets"

    user_timer_status = fields.Char(
        string='Timer Status',
        compute='_user_timer_status',
        help='Current user is working on this Ticket',
    )

    def get_user_id(self):
        """
        Lookup user_id value in decreasing order of importance.
        `original_user_id` is set when a rest API call is made and
        Model.sudo() is called, so the original user can be retrieved.
        """
        ctx = self.env.context
        return ctx.get('original_user_id') or ctx.get('user_id') or self.env.uid

    def get_hr_timesheet_id(self):
        """
        Always return HR Timesheet if one exists for the current Employee and Time period

        If no HR Timesheet exists, and manage_hr_timesheet is True, create it.
        """
        self.ensure_one()
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.get_user_id()),
        ], limit=1)
        if not employee:
            raise UserError('%s is not linked to an Employee Record' % self.env.user.name)

        Param = self.env['ir.config_parameter'].sudo()
        manage_hr_time = Param.get_param('hr_timesheet.manage_hr_timesheet', default=True)

        today = fields.Date.context_today(self)
        TimesheetSheet = self.env['hr_timesheet.sheet'].sudo()
        ts = TimesheetSheet.search(
            [
                ('employee_id', '=', employee.id),
                ('date_start', '<=', today),
                ('date_end', '>=', today),
                ('company_id', '=', self.company_id.id),
            ],
            limit=1,
        )
        if ts:
            return ts.id

        if not manage_hr_time:
            return False

        return TimesheetSheet.with_company(self.company_id.id).create({
            'employee_id': employee.id,
            'company_id': self.company_id.id,
        }).id

    def _update_timesheets(self):
        """
        If the Project or Partner changes,
        then update the Timesheets as well.
        """
        for task in self:
            if not task.timesheet_ids:
                continue

            aa = task.project_id.analytic_account_id
            team = task.project_id.team_id
            company_id = task.company_id.id

            data = {
                'project_id': task.project_id.id,
                'partner_id': task.partner_id.id,
                'analytic_account_id': aa and aa.id,
                'team_id': team and team.id,
                'so_line': None,
                'company_id': company_id,
                'sheet_id': self.get_hr_timesheet_id(),
            }

            # add date field so _get_timesheet_cost method
            # in project_timesheet_currency app doesn't crash
            for ts in task.timesheet_ids:
                data['date'] = ts.date
                ts.with_company(company_id).write(data)

    def _user_timer_status(self):
        for rec in self:
            user_id = rec.get_user_id()
            AccountAnalyticLine = self.env['account.analytic.line'].sudo()
            clocked_in_count = AccountAnalyticLine.search_count([
                ('timer_status', '=', 'running'),
                ('task_id', '=', rec.id),
                ('user_id', '=', user_id),
            ])
            if clocked_in_count > 0:
                rec.user_timer_status = 'running'
                continue

            paused_count = AccountAnalyticLine.search_count([
                ('timer_status', '=', 'paused'),
                ('task_id', '=', rec.id),
                ('user_id', '=', user_id),
            ])
            if paused_count > 0:
                rec.user_timer_status = 'paused'
                continue

            rec.user_timer_status = 'stopped'

    def _pause_active_timers(self):
        """
        Only one timesheet may be active at once per user, so Pause
        other active timers when Starting / Resuming timesheet
        """
        AccountAnalyticLine = self.env['account.analytic.line'].sudo()
        user_clocked_in_task_ids = AccountAnalyticLine.search([
            ('timer_status', '=', 'running'),
            ('user_id', '=', self.get_user_id()),
        ]).mapped('task_id.id')

        for task in self.env['project.task'].search([
            ('id', 'in', user_clocked_in_task_ids),
        ]):
            task.timer_pause()

    def move_or_pause(self, timesheet):
        """
        Check if user is currently active on another timesheet.
        If so, give him the opportunity to move that Timesheet
        to the new Task.
        """
        # Only offer to switch time if user is on the webclient rather than API
        caller = self.env.context.get('caller', 'webclient')
        if caller == 'api':
            timesheet.timer_pause()
            return self._create_timesheet()

        Switcher = self.env['move_timesheet_or_pause.wizard']
        switch = Switcher.create({
            'destination_task_id': self.id,
            'timesheet_id': timesheet.id,
            'origin_task_id': timesheet.task_id.id,
            'ts_action': 'pause',
        })

        wizard_form = self.env.ref('care_center_timesheets.move_timesheet_or_pause', False)

        return {
            'name': 'Move or Pause Timesheet',
            'type': 'ir.actions.act_window',
            'res_model': 'move_timesheet_or_pause.wizard',
            'view_id': wizard_form.id,
            'res_id': switch.id,
            'view_mode': 'form',
            'target': 'new'
        }

    def timer_start(self):
        self.ensure_one()

        # Handle repeated calling (via API)
        if self.timesheet_status_exists(status='running'):
            raise UserError(_('You already have an active timesheet on %s' % self.name))

        if self.timesheet_status_exists(status='paused'):
            return self.timer_resume()

        user = self.env['res.users'].browse(self.get_user_id())
        active_ts = user.get_active_timesheet()

        if active_ts:
            # Only offer to switch time if user is on the webclient rather than API
            caller = self.env.context.get('caller', 'webclient')
            if caller == 'api':
                active_ts.task_id.timer_pause()
                return self._create_timesheet()

            return self.move_or_pause(active_ts)

        return self._create_timesheet()

    def _handle_timesheet_reminder_activity(self, create=True):
        """
        Gets or Creates activity of type 'Sign Out' on the current task & current user
        to remind the user to close all open timesheets at the end of the day.
        """
        self.ensure_one()

        Activity = self.env['mail.activity']
        user_id = self.get_user_id()
        activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'Sign Out')]).mapped('id')
        res_model_id = self.env['ir.model'].search([('model', '=', 'project.task')]).mapped('id')

        if not activity_type_id:
            return

        current_activity = Activity.search([
            ('user_id', '=', user_id),
            ('res_model_id', '=', res_model_id[0]),
            ('res_id', '=', self.id),
            ('activity_type_id', "=", activity_type_id[0]),
        ])

        if current_activity:
            return current_activity

        if not create:
            return

        return Activity.create({
            'activity_type_id': activity_type_id[0],
            'res_id': self.id,
            'res_model_id': res_model_id[0],
            'user_id': user_id,
        })

    def delete_timesheet_reminder_activity(self):
        activity = self._handle_timesheet_reminder_activity(create=False)
        if activity:
            activity.unlink()

    def _create_timesheet(
            self,
            time=0.0,
            timer_status='running',
            name='Work In Progress',
            unit_amount=False,
            factor=False
    ):
        self.ensure_one()
        user_id = self.get_user_id()
        company_id = self.company_id.id

        if not self.project_id.active or not self.project_id.analytic_account_id.active:
            raise UserError(
                'The Project or Account on this task is inactive. '
                'Reactivate the Project before logging new timesheets.'
            )

        Param = self.env['ir.config_parameter'].sudo()
        if not factor:
            factor = self.env['hr_timesheet_invoice.factor'].search([('factor', '=', 0.0)], limit=1)
        offset = float(Param.get_param('start_stop.starting_time_offset', default=0))

        AccountLine = self.env['account.analytic.line'].with_context(sheet_create=True).with_company(company_id)
        timesheet = AccountLine.create({
            'name': name,
            'date_start': datetime.now() - timedelta(minutes=offset),
            'timer_status': timer_status,
            'invoice_status': 'notready',
            'account_id': self.project_id.analytic_account_id.id,
            'user_id': user_id,
            'project_id': self.project_id.id,
            'factor': factor and factor[0].id,
            'sheet_id': self.get_hr_timesheet_id(),
            'company_id': self.company_id.id,
            'task_id': self.id,
            'so_line': None,  # will be set when closing Task
            'full_duration': time,
            'unit_amount': unit_amount,
        })
        if timer_status != 'stopped':
            self._handle_timesheet_reminder_activity()

        return timesheet

    def has_active_timers(self, singleton=False, user_id=None):
        """
        Check for active timesheets before closing / deactivation.
        Or check if a singleton has active timesheets.
        A user can also be specificed for a timesheet
        @param singleton: Bool, whether you want it to check all tasks or just a singleton
        @param user_id: ResUser, whether you also want to see if the active timesheet relates to a specific user
        """
        if not singleton:
            for record in self:
                if record.sudo().has_active_timers(singleton=True):
                    raise UserError('Please close all Running / Paused Timesheets first!')

        return self.timesheet_ids.filtered(
            lambda ts: ts.timer_status in ('running', 'paused') and
            (ts.match_user(user_id) if user_id else True)
        )

    def timesheet_status_exists(self, status):
        """Timesheets of specified status exist"""
        return self.sudo().timesheet_ids.search_count([
            ('timer_status', '=', status),
            ('task_id', '=', self.id),
            ('user_id', '=', self.get_user_id()),
        ]) > 0

    def _get_timesheet_timer(self, status):
        """Get currently running timesheet to Pause / Stop timer"""
        if not self.project_id:
            raise UserError(_('Please specify a project before closing Timesheet.'))

        timesheet = self.sudo().timesheet_ids.search([
            ('timer_status', '=', status),
            ('task_id', '=', self.id),
            ('user_id', '=', self.get_user_id()),
        ])

        if len(timesheet) > 1:
            raise UserError(
                _(
                    'Multiple %s timesheets found for this Ticket/Task. '
                    'Resolve any %s "Work In Progress" timesheet(s) manually.' % (status, status)
                )
            )
        return timesheet

    def _get_current_total_time(self, timesheet):
        """
        When Pausing / Stopping timer, get time of
        current session plus any prior sessions
        """
        end = datetime.now()
        start = fields.Datetime.to_datetime(timesheet.date_start)
        duration = (end - start).total_seconds() / 3600.0
        return timesheet.full_duration + duration

    def timer_pause(self):
        self.ensure_one()
        timesheet = self._get_timesheet_timer(status='running')
        if not timesheet:
            return

        current_total_time = self._get_current_total_time(timesheet)
        timesheet.save_as_last_running()
        timesheet.with_company(self.company_id.id).write({
            'timer_status': 'paused',
            'full_duration': current_total_time,
        })
        return self._user_timer_status()

    def timer_resume(self):
        self.ensure_one()
        self._pause_active_timers()
        timesheet = self._get_timesheet_timer(status='paused')
        if not timesheet:
            return
        timesheet.with_company(self.company_id.id).write({
            'timer_status': 'running',
            'date_start': fields.Datetime.now(),
        })
        self._handle_timesheet_reminder_activity()
        return timesheet

    def timer_stop(self):
        """
        Wizard to close timesheet, but allow the user to
        edit the work description and closing time.
        """
        self.ensure_one()

        timesheet = self._get_timesheet_timer(status='running')
        if not timesheet:
            return
        timesheet.clear_if_previously_running_timesheet()
        wizard_form = self.env.ref('care_center_timesheets.timesheet_timer_wizard', False)
        Timer = self.env['timesheet_timer.wizard']
        completed_timesheets = sum([
            ts.full_duration for ts in self.timesheet_ids if not ts.exclude_from_sale_order
        ])

        new = Timer.create({
            'completed_timesheets': completed_timesheets,
            'date_start': timesheet.date_start,
            'timesheet_id': timesheet.id,
            'factor': timesheet.factor.id,
            'paused_duration': timesheet.full_duration,
        })

        return {
            'name': 'Ticket Timesheet Log',
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet_timer.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def api_timer_stop(self, summary):
        """
        Close timesheet without wizard
        """
        self.ensure_one()
        wip_timesheet = self._get_timesheet_timer(status='running')
        if not wip_timesheet:
            return False

        Timer = self.env['timesheet_timer.wizard']
        completed_timesheets = sum([
            ts.full_duration for ts in self.timesheet_ids if not ts.exclude_from_sale_order
        ])

        new = Timer.create({
            'name': summary,
            'timesheet_id': wip_timesheet.id,
            'completed_timesheets': completed_timesheets,
            'date_start': wip_timesheet.date_start,
            'date_stop': str(datetime.utcnow()),
            'factor': wip_timesheet.factor.id,
            'paused_duration': wip_timesheet.full_duration,
        })

        return new.save_timesheet()
