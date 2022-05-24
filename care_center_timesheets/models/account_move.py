from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        """
        Reset all timesheet invoice statuses
        """
        invoice_ids = [invoice.id for invoice in self if invoice.type == 'out_invoice']

        AccountAnalyticLine = self.env['account.analytic.line'].sudo()
        timesheets = AccountAnalyticLine.search([
            ('timesheet_invoice_id', 'in', invoice_ids),
        ])

        res = super().unlink()
        timesheets.write({'invoice_status': 'ready'})

        return res
