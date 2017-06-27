# coding: utf-8
from odoo import fields, models


class HrTimesheetInvoiceFactor(models.Model):

    _name = "hr_timesheet_invoice.factor"
    _description = "Invoice Rate"
    _order = 'factor,name'

    name = fields.Char('Internal Name', required=True, translate=True)
    factor = fields.Float(
        'Discount (%)',
        default=0.0,
        help="Discount in percentage",
    )
