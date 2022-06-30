from ..utils import get_factored_duration
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

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
    _name = 'account.analytic.line'
    _inherit = [
        'task.duration.fields',
        'account.analytic.line',
    ]

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

    @api.onchange('full_duration', 'factor')
    def _compute_durations(self):
        self.unit_amount = get_factored_duration(
            hours=self.full_duration,
            invoice_factor=self.factor,
        )

    @api.model
    def create(self, vals):
        super_call = super()
        # When creating entries manually, *_status values and set sheet_id
        if ('project_id' in vals or 'task_id' in vals) and not vals.get('timer_status', False):
            task_id = self.env['project.task'].browse(vals.get('task_id', None))
            sheet_id = task_id and task_id.get_hr_timesheet_id()

            vals.update({
                'timer_status': 'stopped',
                'invoice_status': 'notready',
                'sheet_id': sheet_id,
            })

            super_call = super_call.with_context(sheet_create=True)

        return super_call.create(vals)

    def write(self, values):

        locked_fields = LOCK_TS_FIELDS.intersection(values)
        if locked_fields:
            lfields = ', '.join(locked_fields)
            for record in self:
                if record.timesheet_invoice_id:
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

    def pause_timer_if_running(self):
        """
        See if the timesheet was originally running and if so
        set timer_resume to True
        """
        if self.timer_status == 'running':
            self.task_id.timer_pause()
            return True

        return False

    def match_user(self, user_id):
        """
        Check if user_id is related to this timesheet
        @param user_id: ResUser
        @return: Bool, always True if users match else False
        """
        if not user_id:
            return False
        return self.user_id == user_id

    @api.constrains('date', 'employee_id', 'project_id', 'company_id')
    def check_has_timesheet_sheet(self):
        if self.project_id and not self.sheet_id:
            raise ValidationError('This timesheet must be attached to a sheet!')

    def _timesheet_get_sale_line(self):
        """
        Override from sale_timesheet_line_exclude to ensure that notready
        timesheets never have so_line assigned
        """
        self.ensure_one()
        if self.invoice_status == 'notready':
            return self.env['sale.order.line']

        return super()._timesheet_get_sale_line()
