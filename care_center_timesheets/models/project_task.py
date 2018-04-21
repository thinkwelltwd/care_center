# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_invoiceable = fields.Boolean(
        string='Invoiceable',
    )


class ProjectTask(models.Model):

    _name = 'project.task'
    _inherit = ['task.timer', 'project.task']

    ready_to_invoice = fields.Boolean(default=False, copy=False)
    is_invoiceable = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('contract', 'Contract'),
        ('confirm', 'Confirm'),
    ],
        oldname='invoiceable',
        string='Is Invoiceable',
        copy=False,
        default='yes',
        help='Default invoice status for timesheets. Can be '
             'overridden per each timesheet entry.'
    )

    @api.multi
    def write(self, vals):
        task = super(ProjectTask, self).write(vals)

        # widget bar doesn't trigger onchange
        if 'stage_id' in vals:
            self._onchange_stage_id()

        if vals.get('partner_id') or vals.get('project_id'):
            self._update_timesheets()

        return task

    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                record.has_active_timers()
        super(ProjectTask, self).toggle_active()

    @api.multi
    def mark_timesheets_ready(self):
        """
        Mark unready timesheets as ready to invoice.
        This step is once-and-done. The rate of invoicing can be
        controlled by the Factor, but the timesheet will remain ready to invoice.
        This enables the task to be Closed and Re-openned and all new timesheets
        will remain uninvoicable until marked Ready to Invoice
        """
        for task in self:
            new_timesheets = task.timesheet_ids.filtered(
                lambda ts: not ts.timesheet_ready_to_invoice
            )
            new_timesheets.write({'timesheet_ready_to_invoice': True})
            for ts in new_timesheets:
                ts._compute_durations()

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        stage_invoiceable = self.stage_id.is_invoiceable

        if self.ready_to_invoice and not stage_invoiceable:
            self.toggle_ready_to_invoice()

        if stage_invoiceable and self.is_invoiceable == 'yes' and not self.ready_to_invoice:
            self.toggle_ready_to_invoice()

    @api.multi
    def check_invoiceable_stage(self):
        """Don't allow invoiceability to be enabled unless stage is invoiceable"""
        for task in self:
            if not task.stage_id:
                continue
            if not task.ready_to_invoice and not task.stage_id.is_invoiceable:
                raise UserError(
                    'Task cannot be set to Invoiceable in this stage.'
                )

    @api.multi
    def check_task_is_invoiceable(self):
        for task in self:
            # OK to unset invoiceablility
            if task.ready_to_invoice:
                continue
            if task.is_invoiceable != 'yes':
                raise UserError(
                    '"Is Invoiceable" is set to "%s". Must be "Yes" to continue.'
                    % self.is_invoiceable.title()
                )

    @api.multi
    def toggle_ready_to_invoice(self):
        for task in self:
            task.check_invoiceable_stage()
            task.check_task_is_invoiceable()
            task.ready_to_invoice = not task.ready_to_invoice

            if task.ready_to_invoice:
                task.mark_timesheets_ready()

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Set correct sale_line_id from Project Sales Order
        """
        if not self.project_id:
            self.sale_line_id = None
            return

        sale_order = self.env['sale.order'].search([
            ('state', 'not in', ('done', 'cancel')),
            ('related_project_id', '=', self.project_id.analytic_account_id.id),
        ], limit=1, order='confirmation_date')

        so_lines = sale_order.order_line
        service_product = so_lines.filtered(lambda l: l.product_id.invoice_policy != 'order')

        self.sale_line_id = service_product and service_product[0].id
