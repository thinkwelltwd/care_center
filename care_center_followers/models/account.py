from odoo import models


class Invoice(models.Model):
    _name = 'account.move'
    _inherit = [
        'account.move',
        'disable.followers',
    ]
    _followers_key = 'account_followers'

    def action_post(self):
        self = self.with_context(**self.auto_followers_context())
        return super().action_post()


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
