from odoo import api, models


class Invoice(models.Model):
    _name = 'account.invoice'
    _inherit = [
        'account.invoice',
        'disable.followers',
    ]
    _followers_key = 'account_followers'

    def action_invoice_open(self):
        self = self.with_context(**self.auto_followers_context())
        return super().action_invoice_open()


class Payment(models.Model):
    _name = 'account.payment'
    _inherit = [
        'account.payment',
        'disable.followers',
    ]
    _followers_key = 'account_followers'


class PaymentOrder(models.Model):
    _name = 'account.payment.order'
    _inherit = [
        'account.payment.order',
        'disable.followers',
    ]
    _followers_key = 'account_followers'


class Voucher(models.Model):
    _name = 'account.voucher'
    _inherit = [
        'account.voucher',
        'disable.followers',
    ]
    _followers_key = 'account_followers'

