from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    catchall = fields.Boolean(string='Catchall')

    @api.constrains('catchall', 'partner_id')
    def _check_catchall_partner(self):
        for project in self:
            if project.catchall and project.partner_id:
                raise ValidationError(
                    'A Catchall project cannot have a partner set!\
                                        Please remove the partner or uncheck Catchall.'
                )

    @api.onchange('catchall')
    def _onchange_catchall(self):
        if self.catchall and self.partner_id:
            self.partner_id = False


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

    def init(self):
        self._cr.execute("""
        CREATE INDEX IF NOT EXISTS systray_optimize_active_task_user_idx
        ON project_task(user_id) WHERE active = True;
        """)

    def _has_active_timesheets(self):
        for task in self:
            task.has_active_timesheets = task.timesheet_ids.filtered(
                lambda ts: ts.timer_status != 'stopped'
            )

    def write(self, vals):
        task = super(ProjectTask, self).write(vals)

        for record in self:
            if vals.get('partner_id') or vals.get('project_id') or vals.get('sale_line_id'):
                record._update_timesheets()

        return task

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

        invoiceable = self.timesheet_ids.filtered(
            lambda ts: not ts.exclude_from_sale_order and ts.invoice_status != 'invoiced'
        )

        for timesheet in invoiceable:
            so_line = timesheet._timesheet_determine_sale_line()
            timesheet.so_line = so_line and so_line.id

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

    def email_customer(self):
        """
        Open a window to compose an email
        """
        self.ensure_one()
        return self.email_the_customer()

    def email_the_customer(self):
        """
        Helper function to be called from close_task or email_customer.
        Can't be a decorated and be called from other decorated methods
        """

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        if self.env.context.get('closing_task', False):
            name = 'Close'
        else:
            name = 'Ticket Reply'

        template = self.env['mail.template'].search([
            ('name', 'like', name),
            ('model', '=', 'project.task'),
        ], limit=1)
        ctx = {
            'default_model': 'project.task',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template and template.id,
            'default_composition_mode': 'comment',
        }
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

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
        super().close_task()

        if self.env.context.get('email_customer', False):
            return self.email_the_customer()

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
            self.stage_id = done_stage.id

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

        billable_timesheets = self.timesheet_ids.filtered(
            lambda ts: not ts.exclude_from_sale_order
                       and not ts.timesheet_invoice_id
        )
        if billable_timesheets:
            timesheet = billable_timesheets[0]
            timesheet.unit_amount = timesheet.unit_amount + self.remaining_hours
            return

        self.with_context(sheet_create=True).write({
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
                    'so_line': self.sale_line_id and self.sale_line_id.id,
                }
            )]
        })
