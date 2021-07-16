from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def unlink(self):
        """
        Reset all timesheet invoice statuses
        """
        AccountAnalyticLine = self.env['account.analytic.line'].sudo()
        for invoice in self:
            AccountAnalyticLine.search([
                ('timesheet_invoice_id', '=', invoice.id),
            ]).with_context(override_lock_ts_fields=True).write({
                'invoice_status': 'ready',
            })
        return super().unlink()
