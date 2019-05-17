# coding: utf-8
from ..utils import get_factored_duration
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    invoice_status = fields.Selection(selection=[
        ('notready', 'Not Ready'),
        ('ready', 'Ready'),
        ('invoiced', 'Invoiced'),
        ('notinvoiceable', 'Not Invoiceable'),
        ],
        copy=False,
        string='Invoice Status',
        help="Not Ready = Timesheets won't appear in Sales Order \n"
             "Ready = Timesheets will appear in Sales Order \n"
             "Invoiced = No changes can be made to Duration \n"
             "Not Invoiceable = Timesheet cannot be invoiced \n"
    )

    timer_status = fields.Selection(selection=[
        ('stopped', 'Stopped'),
        ('paused', 'Paused'),
        ('running', 'Running'),
        ],
        string='Timer Status')

    date_start = fields.Datetime('Started')
    factor = fields.Many2one(
        'hr_timesheet_invoice.factor',
        'Factor',
        default=lambda s: s.env['hr_timesheet_invoice.factor'].search(
            [('factor', '=', 0.0)], limit=1),
        help="Set the billing percentage when making invoice invoice.",
    )

    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet')

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
            hours=self.full_duration_rounded, invoice_factor=self.factor,
        )
        self.billable_time = round(factored_duration, 2)

    @api.onchange('full_duration', 'factor')
    def _compute_durations(self):
        self.unit_amount = get_factored_duration(
            hours=self.full_duration, invoice_factor=self.factor,
        )

    @api.model
    def create(self, vals):
        # When creating entries manually, *_status values
        if ('project_id' in vals or 'task_id' in vals) and not vals.get('timer_status', False):
            vals.update({
                'timer_status': 'stopped',
                'invoice_status': 'notready',
            })
        task_id = vals.get('task_id', None)
        if task_id:
            task = self.env['project.task'].browse(task_id)
            if task.ready_to_invoice:
                raise ValidationError(
                    'Cannot add new Timesheets to Tasks that are Ready to Invoice.'
                )
        super(AccountAnalyticLine, self).create(vals)

    @api.constrains('unit_amount')
    def check_if_marked_ready(self):
        """
        If a timesheet has been marked as "invoiced",
        the unit_amount should never be changed again.
        """
        ts_type = self._context.get('ts_type', '')
        if self.invoice_status != 'invoiced' or ts_type == 'fulfillment':
            return
        raise ValidationError(
            '"%s" timesheet duration changed!\n\n'
            'Duration may not be changed after timesheet has been invoiced.' %
            self.name
        )

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
