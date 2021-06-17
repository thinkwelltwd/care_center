from odoo import api, fields, models, _
from odoo.tools import config


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    timesheet_invoice_description = fields.Selection(
        '_get_timesheet_invoice_description', default='000'
    )

    @api.model
    def _get_timesheet_invoice_description(self):
        return [
            ('000', _('None')),
            ('111', _('Date - Time spent - Description')),
            ('101', _('Date - Description')),
            ('001', _('Description')),
            ('011', _('Time spent - Description')),
        ]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line_details(self, line, desc_rule):
        details = []
        if desc_rule[0] == '1':
            details.append(fields.Date.to_string(line.date))
        if desc_rule[1] == '1':
            details.append("%s %s" % (round(line.unit_amount, 3), line.product_uom_id.name))
        if desc_rule[2] == '1':
            details.append(line.name)
        return details

    def get_timesheet_lines(self, invoice_status='ready'):
        """
        Return all timesheet lines that reflect work being done even if not invoiceable
        so that the customer can see all the work performed on the ticket.
        """
        domain = [
            ('so_line', '=', self.id),
            ('invoice_status', '=', invoice_status),
        ]
        return self.env['account.analytic.line'].search(domain, order='date, id')

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Get Timesheet description(s) over to Invoice line
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        desc_rule = self.order_id.timesheet_invoice_description
        if not desc_rule or desc_rule == '000':
            return res
        note = []

        timesheets = self.get_timesheet_lines()
        for line in timesheets:
            details = self._prepare_invoice_line_details(line, desc_rule)
            note.append(' - '.join([str(x) or '' for x in details]))

        # This is for not breaking possible tests that expects to create the
        # invoices lines the standard way
        if note and \
                (not config['test_enable'] or self.env.context.get('test_timesheet_description')):
            res['name'] += "\n" + ("\n".join([str(x) or '' for x in note]))

        timesheets.write({'invoice_status': 'invoiced'})

        return res

    @api.multi
    def _compute_analytic(self, domain=None):
        """
        This function writes 'qty_delivered' field to the relevant SO line.

        Only write such lines when the Timesheet is Ready to Invoice.

        The Sale Order should not be in 'to invoice' state until the
        Task has been finished.
        """
        if not domain and self.ids:
            domain = [
                ('so_line', 'in', self.ids),
                ('invoice_status', '=', 'ready'),
            ]

        return super(SaleOrderLine, self)._compute_analytic(domain=domain)

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        """
        Override superclass in /odoo/addons/sale/modules/sale.py (around line 1023) to round 'HALF-UP' on timesheet
        lines to match _get_delivered_quantity_by_analytic() (same file around line 1294).
        """
        for line in self:
            if line.qty_delivered_method != 'timesheet':
                super()._get_invoice_qty()
                continue

            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    line_rounded = invoice_line.uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom, rounding_method='HALF-UP'
                    )
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += line_rounded
                    elif invoice_line.invoice_id.type == 'out_refund':
                        qty_invoiced -= line_rounded
            line.qty_invoiced = qty_invoiced

    @api.depends(
        'qty_invoiced',
        'qty_delivered',
        'product_uom_qty',
        'order_id.state',
    )
    def _get_to_invoice_qty(self):
        """
        Override super to subtract timesheets that are not ready to be invoiced addons/sale/models/sale.py (around line
        1035).
        """
        res = super()._get_to_invoice_qty()
        lines = self.filtered(lambda l: l.qty_delivered_method == 'timesheet')
        for line in lines:
            timesheet_ids = line.get_timesheet_lines(invoice_status='notready')
            if not timesheet_ids:
                continue
            line.qty_to_invoice = line.qty_to_invoice - round(
                sum(timesheet_ids.mapped('unit_amount')), 2
            )
        return res
