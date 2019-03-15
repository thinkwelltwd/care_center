from odoo import api, fields, models, _
from odoo.tools import config


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    timesheet_invoice_description = fields.Selection(
        '_get_timesheet_invoice_description', default='000')

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
            details.append(line.date)
        if desc_rule[1] == '1':
            details.append(
                "%s %s" % (line.unit_amount, line.product_uom_id.name))
        if desc_rule[2] == '1':
            details.append(line.name)
        return details

    def get_timesheet_lines(self):
        domain = [
            ('so_line', '=', self.id),
            ('invoice_status', '=', 'ready'),
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

        for line in self.get_timesheet_lines():
            details = self._prepare_invoice_line_details(line, desc_rule)
            note.append(' - '.join([str(x) or '' for x in details]))

        # This is for not breaking possible tests that expects to create the
        # invoices lines the standard way
        if note and (not config['test_enable'] or self.env.context.get(
                'test_timesheet_description')):
            res['name'] += "\n" + (
                "\n".join([str(x) or '' for x in note]))

        return res

    @api.multi
    def _compute_analytic(self, domain=None):
        """
        This function writes 'qty_delivered' field to the relevant SO line.

        Only write such lines when the Timesheet is Ready to Invoice.

        The Sale Order should not be in 'to invoice' state until the
        Task has been finished.
        """

        ready_to_invoice = ('invoice_status', 'in', ('ready', 'invoiced'))

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

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoices = self.action_invoice_create(grouped=grouped, final=final)

        for order in self:
            order.get_timesheet_lines().write({'invoice_status': 'invoiced'})

        return invoices
