# -*- coding: utf-8 -*-


def migrate(cr, version):
    if not version:
        return
    cr.execute('UPDATE account_analytic_line SET invoice_status=temporary_invoice_status')
    cr.execute('ALTER TABLE account_analytic_line DROP COLUMN temporary_invoice_status')
