from odoo import api, models


class Phonecall(models.Model):
    _name = 'crm.phonecall'
    _inherit = [
        'crm.phonecall',
        'disable.followers',
    ]
    _followers_key = 'sale_followers'


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = [
        'sale.order',
        'disable.followers',
    ]
    _followers_key = 'sale_followers'


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = [
        'sale.order',
        'disable.followers',
    ]
    _followers_key = 'sale_followers'

    @api.multi
    def action_confirm(self):
        self = self.with_context(**self.auto_followers_context())
        return super().action_confirm()
