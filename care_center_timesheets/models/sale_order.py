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

    def _prepare_invoice_line_details(self, line, desc_rule):
        details = []
        if desc_rule[0] == '1':
            details.append(fields.Date.to_string(line.date))
        if desc_rule[1] == '1':
            details.append("%s %s" % (round(line.unit_amount, 3), line.product_uom_id.name))
        if desc_rule[2] == '1':
            details.append(line.name)
        return details

    def _prepare_invoice_line(self, qty):
        """
        Get Timesheet description(s) over to Invoice line
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        desc_rule = self.order_id.timesheet_invoice_description
        if not desc_rule or desc_rule == '000':
            return res
        note = []

        domain = [
            ('so_line', '=', self.id),
            # the module sale_timesheet_invoice_description on which this functionality is based
            # but rather filters by whether or not the timesheet is older than any prior invoices
            # that filter is problematic, as it excludes timesheets that might've been open for
            # some time before marked as Ready to Invoice.
            # And no filter other than `so_line` is problematic too, as old lines already billed
            # can get their descriptions inserted, so this seems to work well.
            ('timesheet_invoice_id', '=', False),
        ]
        timesheets = self.env['account.analytic.line'].search(domain, order='date, id')

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
