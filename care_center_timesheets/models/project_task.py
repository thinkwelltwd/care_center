from odoo import api, models, fields
from odoo.exceptions import UserError


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_invoiceable = fields.Boolean(string='Invoiceable')


class ProjectTask(models.Model):

    _name = 'project.task'
    _description = 'Care Center Timesheets Project Task'
    _inherit = ['task.timer', 'project.task']

    has_active_timesheets = fields.Boolean(
        string='Active Timesheets',
        compute='_has_active_timesheets',
    )

    @api.multi
    def _has_active_timesheets(self):
        for task in self:
            task.has_active_timesheets = task.timesheet_ids.filtered(
                lambda ts: ts.timer_status != 'stopped'
            )

    @api.multi
    def write(self, vals):
        task = super(ProjectTask, self).write(vals)

        for record in self:
            if vals.get('partner_id') or vals.get('project_id'):
                record._update_timesheets()

        return task

    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                record.has_active_timers()
        super(ProjectTask, self).toggle_active()

    @api.model
    def mark_timesheets_ready(self):
        """
        Mark unready timesheets as ready to invoice.
        This step is once-and-done. The rate of invoicing can be
        controlled by the Factor, but the timesheet will remain ready to invoice.
        This enables the task to be Closed and Re-opened and all new timesheets
        will remain `notready` until marked Ready to Invoice
        """
        new_timesheets = self.timesheet_ids.filtered(lambda ts: ts.invoice_status == 'notready')
        new_timesheets.write({'invoice_status': 'ready'})

    def timesheet_factor_unconfirmed(self):
        """
        Don't change allow switching to an invoiceable stage
        if Task has timesheets with invoiceable factor of "Confirm"
        """
        unconfirmed_ts = self.timesheet_ids.filtered(lambda ts: ts.factor.name == 'Confirm')
        if unconfirmed_ts:
            raise UserError('Please finalize Invoice Factor on all Confirm timesheets.')

    def timesheets_active(self):
        """
        Don't change allow switching to an invoiceable stage
        if Task has timesheets that aren't Stopped
        """
        if self.has_active_timesheets:
            raise UserError('Please stop all Running / Paused timesheets.')

    @api.multi
    def close_task(self):
        """
        Close Task, timesheets and set stage.
        """
        self.ensure_one()
        self.timesheets_active()
        self.timesheet_factor_unconfirmed()
        self.set_done_stage()
        self.add_planned_expected_difference()
        self.sudo().mark_timesheets_ready()
        if self.active:
            self.toggle_active()

    def set_done_stage(self):
        """Set stage to Done or other invoiceable stage"""
        if self.stage_id and self.stage_id.is_invoiceable:
            return

        done_stage = self.env['project.task.type'].search(
            [
                ('name', '=', 'Done'),
                ('is_invoiceable', '=', True),
            ],
            limit=1,
        )
        if done_stage:
            self.write({'stage_id': done_stage.id})

    @api.model
    def add_planned_expected_difference(self):
        """
        When there's planned_hours, check to see if effective_hours are lower.
        If so, customer should be invoiced for planned_hours as tech was
        efficient in performing work.

        Add timesheet indicating fulfillment, so customer is invoiced
        for the full amount planned of time.
        """
        if self.remaining_hours <= 0:
            return

        self.write({
            'timesheet_ids': [(
                0,
                0,
                {
                    'name': 'Task / Contract Fulfillment',
                    'full_duration': 0,  # keep 0 to report on staff efficiency
                    'unit_amount': self.remaining_hours,
                    'invoice_status': 'ready',
                    'timer_status': 'stopped',
                    'factor': False,  # No factor, because we invoice at full amount
                    'user_id': self.env.uid,
                    'account_id': self.project_id.analytic_account_id.id,
                    'project_id': self.project_id.id,
                    'sheet_id': self.get_hr_timesheet_id(),
                }
            )]
        })

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Set correct sale_line_id from Project Sales Order
        """
        if not self.project_id:
            self.sale_line_id = None
            return

        sale_order = self.env['sale.order'].search(
            [
                ('state', 'not in', ('done', 'cancel')),
                ('analytic_account_id', '=', self.project_id.analytic_account_id.id),
            ],
            limit=1,
            order='confirmation_date',
        )

        so_lines = sale_order.order_line
        service_product = so_lines.filtered(lambda l: l.product_id.invoice_policy != 'order')

        self.sale_line_id = service_product and service_product[0].id
