# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _compute_analytic(self, domain=None):
        """
        This function writes 'qty_delivered' field to the relevant SO line.

        Only write such lines when the Timesheet is Ready to Invoice.

        The Sale Order should not be in 'to invoice' state until the
        Task has been finished.
        """

        ready_to_invoice = ('timesheet_ready_to_invoice', '=', True)

        if not domain and self.ids:
            domain = [
                ('so_line', 'in', self.ids),
                ready_to_invoice,
                '|',
                ('amount', '<=', 0.0),
                ('project_id', '!=', False),
                ready_to_invoice,
            ]

        return super(SaleOrderLine, self)._compute_analytic(domain=domain)
