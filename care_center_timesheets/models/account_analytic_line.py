# coding: utf-8
from ..utils import get_factored_duration
from odoo import fields, models, api, _



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    timesheet_ready_to_invoice = fields.Boolean(default=False, copy=False)

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
        oldname='to_invoice',
        help="Allows setting the discount while making invoice, keep"
        " empty if the activities should not be invoiced.")

    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet')

    @api.onchange('full_duration', 'factor', 'timesheet_ready_to_invoice')
    def _compute_durations(self):
        if not self.timesheet_ready_to_invoice:
            self.unit_amount = 0.0
            return
        self.unit_amount = get_factored_duration(
            hours=self.full_duration, invoice_factor=self.factor,
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
