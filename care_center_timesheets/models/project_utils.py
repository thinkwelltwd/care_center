# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectUtils(models.AbstractModel):
    _name = 'project.utils'
    _description = "Utils for Issues and Tasks"

    invoiceable = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('contract', 'Contract'),
        ('confirm', 'Confirm'),
    ],
        string='Invoicable',
        default='yes',
        help='Default invoice status for timesheets. Can be '
             'overridden per each timesheet entry.'
    )

    user_timer_status = fields.Char(
        string='Timer Status',
        compute='_user_timer_status',
        help='Current user is working on this Issue',
    )

    @api.one
    def _user_timer_status(self):
        clocked_in_count = self.timesheet_ids.search_count([
            ('timer_status', '=', 'running'),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_count > 0:
            self.user_timer_status = 'running'
            return

        paused_count = self.timesheet_ids.search_count([
            ('timer_status', '=', 'paused'),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if paused_count > 0:
            self.user_timer_status = 'paused'
            return

        self.user_timer_status = 'stopped'

    @api.one
    def _prevent_multiple_clocked_in(self):

        clocked_in_somewhere = self.timesheet_ids.search_count([
            ('timer_status', '=', 'running'),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_somewhere:
            raise UserError(_(
                'You are already working and can\'t record multiple timesheets at once.\n '
                'Check the "My Timers" filter and Stop other timer(s).'
            ))

    @api.multi
    def timer_start(self):

        self._prevent_multiple_clocked_in()

        Factor = self.env['hr_timesheet_invoice.factor']
        if not self.invoiceable or self.invoiceable == 'yes':
            factor = Factor.search([('name', '=', 'Yes')])
        elif self.invoiceable == 'confirm':
            factor = Factor.search([('name', '=', 'Confirm')])
        else:
            factor = Factor.search([('name', '=', 'No')])
        factor = factor and factor[0].id

        self.write({
            'timesheet_ids': [(0, 0, {
                'name': 'Work In Progress',
                'date_start': datetime.now(),
                'timer_status': 'running',
                'account_id': self.project_id.analytic_account_id.id,
                'user_id': self.env.uid,
                'project_id': self.project_id.id,
                'to_invoice': factor,
             })]
        })

    def _get_timesheet(self, status):
        """Get currently running timesheet to Pause / Stop timer"""
        if not self.project_id:
            raise UserError(_(
                'Please specify a project before closing Timesheet.'
            ))

        timesheet = self.timesheet_ids.search([
            ('timer_status', '=', status),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if not timesheet:
            raise UserError(_(
                'You have no "%s" timesheet!' % status
            ))
        if len(timesheet) > 1:
            raise UserError(_(
                'Multiple %s timesheets found for this Issue/Task. '
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
        timesheet = self._get_timesheet(status='running')
        current_total_time = self._get_current_total_time(timesheet)
        timesheet.write({
            'timer_status': 'paused',
            'full_duration': current_total_time,
        })
        self._user_timer_status()

    @api.multi
    def timer_resume(self):
        self._prevent_multiple_clocked_in()
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
        timesheet = self._get_timesheet(status='running')

        wizard_form = self.env.ref('care_center_timesheets.timesheet_timer_wizard', False)
        Timer = self.env['timesheet_timer.wizard']

        new = Timer.create({
            'completed_timesheets': sum([ts.full_duration for ts in self.timesheet_ids]),
            'timesheet_id': timesheet.id,
            'to_invoice': timesheet.to_invoice.id,
        })

        return {
            'name': 'Record Issue Timesheet Log',
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet_timer.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
