# -*- coding: utf-8 -*-
from odoo import models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    @api.multi
    def _pause_active_timers(self):
        """
        Pause Active Timers
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
    def attendance_action_change(self):
        """
        Pause active Timesheet when signing out
        """
        current_attendance_state = self.attendance_state
        attendance = super(HrEmployee, self).attendance_action_change()

        if current_attendance_state == 'checked_in':
            self._pause_active_timers()

        return attendance
