from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})

    SaleOrder = env['sale.order']
    for so in SaleOrder.search([('state', '=', 'sale'), ('project_id', '!=', False)]):
        if not so.invoice_ids or not so.project_id:
            continue
        for line in so.order_line:
            if line.product_id.track_service not in ['timesheet', 'task']:
                continue
            timesheets = env['account.analytic.line'].search([
                ('so_line', '=', line.id),
                ('amount', '<=', 0.0),
                ('invoice_status', '!=', 'invoiced'),
            ])
            if not timesheets:
                continue
            if line.qty_delivered == line.qty_invoiced:
                timesheets.write({'invoice_status': 'invoiced'})
                env.cr.commit()
