from datetime import datetime, timedelta
from ..utils import get_factored_duration, round_timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TimesheetTimerWizard(models.TransientModel):
    _name = 'timesheet_timer.wizard'
    _description = 'Timesheet Timer'

    name = fields.Char(string='Work Description')
    date_stop = fields.Datetime(string='Stop Time')
    completed_timesheets = fields.Float(string='Time So Far')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet')

    to_invoice = fields.Many2one(
        'hr_timesheet_invoice.factor',
        'Invoiceable',
        default=lambda s: s.env['hr_timesheet_invoice.factor'].search(
            [], order='factor asc', limit=1),
        help="Allows setting the discount while making invoice."
        " Set to 'No' if the time should not be invoiced.")
    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet')
    unit_amount = fields.Float(
        'Duration',
        default=0.0,
        help='Invoiceable amount of time spent on timesheet')

    @api.onchange('name', 'date_stop', 'to_invoice')
    def timesheet_stats(self):
        """
        Display calculated data to the user, and return a dict
        of data to save the timesheet.
        """
        start = fields.Datetime.from_string(self.timesheet_id.date_start)
        stop = fields.Datetime.from_string(self.date_stop) or datetime.now()

        this_timesheet = self.get_minimum_duration(
            duration=self.get_timesheet_duration(start, stop)
        )

        rounded_time = round_timedelta(
            td=timedelta(seconds=this_timesheet * 3600),
            period=self.get_rounded_minutes(),
        )

        self.full_duration = rounded_time.total_seconds() / 3600.0
        self.unit_amount = get_factored_duration(self.full_duration, self.to_invoice)

        return {
            'name': self.name,
            'timer_status': 'stopped',
            'full_duration': self.full_duration,
            'to_invoice': self.to_invoice.id,
            'unit_amount': self.unit_amount,
        }

    @api.constrains('name')
    def _check_name(self):
        if not self.name:
            raise ValidationError(_(
                'Please enter work description before closing Timesheet.'
            ))

    @api.constrains('date_stop')
    def _check_date_stop(self):
        # Only test if user provides a value in the form
        if self.date_stop:
            start = fields.Datetime.from_string(self.timesheet_id.date_start)
            stop = fields.Datetime.from_string(self.date_stop)
            if stop < start:
                raise ValidationError(_(
                    'Stop time must be later than Start time'
                ))

    def get_timesheet_duration(self, start, stop):
        """
        Get complete timesheet duration. full_duration is populated
        from Pause / Resume cycles, so include full_duration
        """
        duration = (stop - start).total_seconds() / 3600
        return self.timesheet_id.full_duration + duration

    def get_minimum_duration(self, duration):
        """
        Projects / Tasks can have a minimum total turation

        :param duration: Duration of this ticket in hours
        """
        Param = self.env['ir.config_parameter']
        work_log_min = float(Param.get_param('start_stop.minimum_work_log', default=0))
        total_minutes = (self.completed_timesheets + duration) * 60

        if work_log_min and total_minutes < work_log_min:
            return work_log_min / 60

        return duration

    def get_rounded_minutes(self):
        """
        Timesheets are rounded per minimum minutes on entire Ticket / Task,
        and if that minumimum is reached, then minimum time per timesheet
        """
        Param = self.env['ir.config_parameter']
        minutes = float(Param.get_param('start_stop.minutes_increment', default=0))
        return timedelta(seconds=minutes * 60)

    @api.multi
    def save_timesheet(self):
        """
        'write' method wants to return a view so, we use custom function
        so that we can just go back to current Ticket/Task page
        """

        # re-call stats because we didn't persist the wizard
        self.timesheet_id.write(self.timesheet_stats())

        return True
