# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TaskTimer(models.AbstractModel):
    _name = 'task.timer'
    _description = "Utils for Tasks / Tickets"

    user_timer_status = fields.Char(
        string='Timer Status',
        compute='_user_timer_status',
        help='Current user is working on this Ticket',
    )

    @api.multi
    def _update_timesheets(self):
        """
        If the Project or Partner changes,
        then update the Timesheets as well.
        """
        for task in self:
            aa = task.project_id.analytic_account_id
            team = task.project_id.team_id

            data = {
                'project_id': task.project_id.id,
                'partner_id': task.partner_id.id,
                'analytic_account_id': aa and aa.id,
                'team_id': team and team.id,
                'so_line': None,
            }

            # add date field so _get_timesheet_cost method
            # in project_timesheet_currency app doesn't crash
            for ts in task.timesheet_ids:
                data['date'] = ts.date
                ts.write(data)

    @api.one
    def _user_timer_status(self):
        clocked_in_count = self.env['account.analytic.line'].search_count([
            ('timer_status', '=', 'running'),
            ('task_id', '=', self.id),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_count > 0:
            self.user_timer_status = 'running'
            return

        paused_count = self.env['account.analytic.line'].search_count([
            ('timer_status', '=', 'paused'),
            ('task_id', '=', self.id),
            ('user_id', '=', self.env.uid),
        ])
        if paused_count > 0:
            self.user_timer_status = 'paused'
            return

        self.user_timer_status = 'stopped'

    @api.multi
    def _pause_active_timers(self):
        """
        Only one timesheet may be active at once per user, so Pause
        other active timers when Starting / Resuming timesheet
        """
        user_clocked_in_task_ids = self.env['account.analytic.line'].search([
            ('timer_status', '=', 'running'),
            ('user_id', '=', self.env.uid),
        ]).mapped('task_id.id')

        for task in self.env['project.task'].search([
            ('id', 'in', user_clocked_in_task_ids),
        ]):
            task.timer_pause()

    @api.multi
    def get_hr_timesheet_id(self):
        """
        Always return HR Timesheet if one exists for the current Employee and Time period

        If no HR Timesheet exists, and manage_hr_timesheet is True, create it.
        """
        self.ensure_one()
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid),
        ])
        if not employee:
            raise UserError('%s is not linked to an Employee Record' % self.env.user.name)

        manage_hr_time = self.env['ir.config_parameter'].get_param(
            'hr_timesheet.manage_hr_timesheet',
            default=True
        )

        today = fields.Date.context_today(self)
        ts = self.env['hr_timesheet_sheet.sheet'].search([
            ('employee_id', '=', employee.id),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ])
        if ts:
            return ts.id

        if not manage_hr_time:
            return False

        return self.env['hr_timesheet_sheet.sheet'].create({
            'employee_id': employee.id
        }).id

    @api.multi
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
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    @api.multi
    def timer_start(self):
        self.ensure_one()

        # Handle repeated calling (via API)
        if self.timesheet_status_exists(status='running'):
            raise UserError(_(
                'You already have an active timesheet on %s' % self.name
            ))

        if self.timesheet_status_exists(status='paused'):
            self.timer_resume()
            return

        active_ts = self.env['account.analytic.line'].search([
            ('timer_status', '=', 'running'),
            ('task_id', '!=', self.id),
            ('user_id', '=', self.env.uid),
        ], limit=1)

        if active_ts:
            # Only offer to switch time if user is on the webclient rather than API
            caller = self.env.context.get('caller', 'webclient')
            if caller == 'api':
                active_ts.task_id.timer_pause()
                return self._create_timesheet()

            return self.move_or_pause(active_ts)

        self._create_timesheet()

    @api.multi
    def _create_timesheet(self):
        self.ensure_one()
        factor = self.env['hr_timesheet_invoice.factor'].search([('factor', '=', 100.0)], limit=1)
        offset = float(
            self.env['ir.config_parameter'].get_param('start_stop.starting_time_offset', default=0)
        )

        self.write({
            'timesheet_ids': [(0, 0, {
                'name': 'Work In Progress',
                'date_start': datetime.now() - timedelta(minutes=offset),
                'timer_status': 'running',
                'account_id': self.project_id.analytic_account_id.id,
                'user_id': self.env.uid,
                'project_id': self.project_id.id,
                'factor': factor and factor[0].id,
                'sheet_id': self.get_hr_timesheet_id(),
             })]
        })

    @api.multi
    def has_active_timers(self):
        """
        Check for active timesheets before closing / deactivation
        """
        for record in self:
            if record.timesheet_ids.filtered(lambda ts: ts.timer_status in ('running', 'paused')):
                raise UserError('Please close all Running / Paused Timesheets first!')

    def timesheet_status_exists(self, status):
        """Timesheets of specified status exist"""
        return self.timesheet_ids.search_count([
            ('timer_status', '=', status),
            ('task_id', '=', self.id),
            ('user_id', '=', self.env.uid),
        ]) > 0

    def _get_timesheet(self, status):
        """Get currently running timesheet to Pause / Stop timer"""
        if not self.project_id:
            raise UserError(_(
                'Please specify a project before closing Timesheet.'
            ))

        timesheet = self.timesheet_ids.search([
            ('timer_status', '=', status),
            ('task_id', '=', self.id),
            ('user_id', '=', self.env.uid),
        ])
        if not timesheet:
            raise UserError(_(
                'You have no "%s" timesheet!' % status
            ))
        if len(timesheet) > 1:
            raise UserError(_(
                'Multiple %s timesheets found for this Ticket/Task. '
                'Resolve any %s "Work In Progress" timesheet(s) manually.' % (status, status)
            ))
        return timesheet

    def _get_current_total_time(self, timesheet):
        """
        When Pausing / Stopping timer, get time of
        current session plus any prior sessions
        """
        end = datetime.now()
        start = fields.Datetime.from_string(timesheet.date_start)
        duration = (end - start).total_seconds() / 3600.0
        return timesheet.full_duration + duration

    @api.multi
    def timer_pause(self):
        self.ensure_one()
        timesheet = self._get_timesheet(status='running')
        current_total_time = self._get_current_total_time(timesheet)
        timesheet.write({
            'timer_status': 'paused',
            'full_duration': current_total_time,
        })
        self._user_timer_status()

    @api.multi
    def timer_resume(self):
        self.ensure_one()
        self._pause_active_timers()
        timesheet = self._get_timesheet(status='paused')
        timesheet.write({
            'timer_status': 'running',
            'date_start': fields.Datetime.now(),
        })

    @api.multi
    def timer_stop(self):
        """
        Wizard to close timesheet, but allow the user to
        edit the work description and closing time.
        """
        self.ensure_one()
        timesheet = self._get_timesheet(status='running')

        wizard_form = self.env.ref('care_center_timesheets.timesheet_timer_wizard', False)
        Timer = self.env['timesheet_timer.wizard']

        new = Timer.create({
            'completed_timesheets': sum([ts.full_duration for ts in self.timesheet_ids]),
            'timesheet_id': timesheet.id,
            'factor': timesheet.factor.id,
        })

        return {
            'name': 'Ticket Timesheet Log',
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet_timer.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
