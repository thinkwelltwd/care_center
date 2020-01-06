from datetime import timedelta
from ..utils import get_factored_duration, round_timedelta
from odoo import fields, models, api
from odoo.exceptions import UserError

# Fields that cannot be changed after
# timesheet line is invoiced.
LOCK_TS_FIELDS = {
    'factor',
    'full_duration',
    'invoice_status',
    'partner_id',
    'project_id',
    'task_id',
    'unit_amount',
    'exclude_from_sale_order',
}


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    invoice_status = fields.Selection(
        selection=[
            ('notready', 'Not Ready'),
            ('ready', 'Ready'),
            ('invoiced', 'Invoiced'),
        ],
        copy=False,
        string='Invoice Status',
        help="Not Ready = Timesheets won't appear in Sales Order \n"
        "Ready = Timesheets will appear in Sales Order \n"
        "Invoiced = No changes can be made to Duration \n"
        "Not Invoiceable = Timesheet cannot be invoiced \n",
    )

    timer_status = fields.Selection(
        selection=[
            ('stopped', 'Stopped'),
            ('paused', 'Paused'),
            ('running', 'Running'),
        ],
        string='Timer Status',
    )

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

    @api.one
    @api.depends('full_duration')
    def _round_full_duration(self):
        self.full_duration_rounded = round(self.full_duration, 2)

    @api.one
    @api.depends('full_duration_rounded')
    def _get_billable_time(self):
        factored_duration = get_factored_duration(
            hours=self.full_duration_rounded,
            invoice_factor=self.factor,
        )
        self.billable_time = round(factored_duration, 2)

    @api.onchange('factor')
    def _set_factor(self):
        if self.factor and float(self.factor.factor) == 100.0:
            self.exclude_from_sale_order = True
            self._onchange_exclude_from_sale_order()

    @api.onchange('full_duration', 'factor')
    def _compute_durations(self):
        self.unit_amount = get_factored_duration(
            hours=self.full_duration,
            invoice_factor=self.factor,
        )

    @api.model
    def create(self, vals):
        # When creating entries manually, *_status values
        if ('project_id' in vals or 'task_id' in vals) and not vals.get('timer_status', False):
            vals.update({
                'timer_status': 'stopped',
                'invoice_status': 'notready',
            })
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, values):

        locked_fields = LOCK_TS_FIELDS.intersection(values)
        if locked_fields:
            lfields = ', '.join(locked_fields)
            for record in self:
                if record.invoice_status == 'invoiced':
                    raise UserError(
                        f'Field(s) "{lfields}"" cannot be changed after timesheet is invoiced!'
                    )

        return super(AccountAnalyticLine, self).write(values)

    @api.model
    def save_as_last_running(self):
        """
        Save current active timesheet as last running timesheet
        in preparation to switching to another task timesheet.
        """
        if self.id != self.user_id.previous_running_timesheet.id:
            self.user_id.write({'previous_running_timesheet': self.id})

    @api.model
    def clear_if_previously_running_timesheet(self):
        """
        Clear user's record of the previous running timesheet
        if this timesheet was the previous active one.
        """
        if self.id == self.user_id.previous_running_timesheet.id:
            self.user_id.write({'previous_running_timesheet': False})

    def get_timesheet_duration(self, stop=None):
        """
        Get complete timesheet duration. full_duration is populated
        from Pause / Resume cycles, so include full_duration
        """
        start = fields.Datetime.to_datetime(self.date_start)
        stop = stop or fields.Datetime.now()
        current_duration = (stop - start).total_seconds() / 60.0
        full_duration_minutes = self.full_duration * 60.0
        all_duration = full_duration_minutes + current_duration

        return round_timedelta(
            td=timedelta(minutes=all_duration),
            period=self.get_rounded_minutes(),
        ).total_seconds() / 3600.0

    def get_rounded_minutes(self):
        """
        Timesheets are rounded per minimum minutes on entire Ticket / Task,
        and if that minimum is reached, then minimum time per timesheet
        """
        Param = self.env['ir.config_parameter'].sudo()
        minutes = float(Param.get_param('start_stop.minutes_increment', default=0))
        return timedelta(minutes=minutes)

    def _get_timesheet_cost(self, values):
        """
        Lifted from sale_timesheet, so we can base cost on undiscounted
        amount of time, while invoicing on discounted amount
        """
        values = values if values is not None else {}
        if values.get('project_id') or self.project_id:
            if values.get('amount'):
                return {}
            fd = values.get('full_duration', 0.0) or self.full_duration
            user_id = values.get('user_id') or self.user_id.id or self._default_user()
            user = self.env['res.users'].browse([user_id])
            emp = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
            cost = emp and emp.timesheet_cost or 0.0
            uom = (emp or user).company_id.project_time_mode_id
            # Nominal employee cost = 1 * company project UoM (project_time_mode_id)
            return {
                'amount': -fd * cost,
                'product_uom_id': uom.id,
                'account_id': values.get('account_id') or self.account_id.id or emp.account_id.id,
            }
        return {}

    @api.multi
    def move_or_split(self):
        """
        Give opportunity to split time between two timesheets or move entire
        timesheet to the new Task.
        """

        Switcher = self.env['move_timesheet_or_split.wizard']
        switch = Switcher.create({
            'timesheet_id': self.id,
            'origin_task_id': self.task_id.id,
            'ts_action': 'split',
        })

        wizard_form = self.env.ref('care_center_timesheets.move_timesheet_or_split', False)

        return {
            'name': 'Move Timesheet or Split',
            'type': 'ir.actions.act_window',
            'res_model': 'move_timesheet_or_split.wizard',
            'view_id': wizard_form.id,
            'res_id': switch.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    @api.multi
    def pause_timer_if_running(self):
        """
        See if the timesheet was originally running and if so
        set timer_resume to True
        """
        if self.timer_status == 'running':
            self.task_id.timer_pause()
            return True

        return False
