from ..utils import get_factored_duration

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class TimesheetTimerWizard(models.TransientModel):
    _name = 'timesheet_timer.wizard'
    _description = 'Timesheet Timer'

    name = fields.Char(string='Work Description')
    date_stop = fields.Datetime(string='Stop Time')
    completed_timesheets = fields.Float(string='Hours So Far')
    timesheet_id = fields.Many2one(
        'account.analytic.line',
        string='Timesheet',
    )

    factor = fields.Many2one(
        'hr_timesheet_invoice.factor',
        'Factor',
        default=lambda s: s.env['hr_timesheet_invoice.factor'].search(
            [('factor', '=', 0.0)],
            limit=1,
        ),
        required=True,
        help="Allows setting the discount while making invoice."
        " Set to 'No' if the time should not be invoiced."
    )
    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet',
    )
    unit_amount = fields.Float(
        'Duration',
        default=0.0,
        help='Invoiceable amount of time spent on timesheet',
    )

    @api.onchange('name', 'date_stop', 'factor')
    def timesheet_stats(self):
        """
        Display calculated data to the user, and return a dict
        of data to save the timesheet.
        """
        stop = fields.Datetime.to_datetime(self.date_stop) or fields.Datetime.now()
        timesheet_duration = self.timesheet_id.get_timesheet_duration(stop=stop)
        self.full_duration = self.get_minimum_duration(timesheet_duration)
        self.unit_amount = get_factored_duration(self.full_duration, self.factor)

        return {
            'name': self.name,
            'timer_status': 'stopped',
            'full_duration': self.full_duration,
            'factor': self.factor.id,
            'unit_amount': self.unit_amount,
        }

    @api.constrains('name')
    def _check_name(self):
        if not self.name:
            raise ValidationError(_('Please enter work description before closing Timesheet.'))

    @api.constrains('date_stop')
    def _check_date_stop(self):
        # Only test if user provides a value in the form
        if self.date_stop:
            start = fields.Datetime.to_datetime(self.timesheet_id.date_start)
            stop = fields.Datetime.to_datetime(self.date_stop)
            if stop < start:
                raise ValidationError(_('Stop time must be later than Start time'))

    def get_minimum_duration(self, duration):
        """
        Projects / Tasks can have a minimum total duration

        :param duration: Duration of this ticket in hours
        """
        # Sometimes a ticket really shouldn't have a minimum
        # duration especially on internal communications
        if not self.env.context.get('calculate_minimum_duration', True):
            return duration

        Param = self.env['ir.config_parameter'].sudo()
        work_log_min = float(Param.get_param('start_stop.minimum_work_log', default=0)) / 60
        if not work_log_min:
            return duration

        all_timesheets = self.completed_timesheets + duration

        if all_timesheets < work_log_min:
            return duration + (work_log_min - duration)

        return duration

    @api.multi
    def save_timesheet(self):
        """
        'write' method wants to return a view so, we use custom function
        so that we can just go back to current Ticket/Task page
        """

        # re-call stats because we didn't persist the wizard
        company_id = self.timesheet_id.company_id.id
        data = self.timesheet_stats()
        self.sudo().with_context(force_company=company_id).timesheet_id.write(data)
        self.timesheet_id.task_id.delete_timesheet_reminder_activity()

        return self.timesheet_id
