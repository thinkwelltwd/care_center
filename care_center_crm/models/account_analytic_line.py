from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    phonecall_id = fields.Many2one(
        comodel_name='crm.phonecall',
        string='Phone Call',
    )
