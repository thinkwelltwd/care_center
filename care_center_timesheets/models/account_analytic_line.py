# coding: utf-8
from ..utils import get_duration, get_factored_duration
from odoo import fields, models, api, _



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    date_start = fields.Datetime('Started')
    date_stop = fields.Datetime('Stopped')

    to_invoice = fields.Many2one(
        'hr_timesheet_invoice.factor',
        'Invoiceable',
        default=lambda s: s.env['hr_timesheet_invoice.factor'].search(
            [], order='factor asc', limit=1),
        help="Allows setting the discount while making invoice, keep"
        " empty if the activities should not be invoiced.")

    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet')

    @api.onchange('date_start', 'date_stop')
    def _compute_duration(self):
        if self.date_start and self.date_stop:
            self.full_duration = get_duration(
                start=fields.Datetime.from_string(self.date_start),
                stop=fields.Datetime.from_string(self.date_stop),
            )

    @api.onchange('full_duration', 'to_invoice')
    def _compute_durations(self):
        self.unit_amount = get_factored_duration(
            hours=self.full_duration, invoice_factor=self.to_invoice,
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
