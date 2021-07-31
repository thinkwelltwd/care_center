from odoo import models


class Product(models.Model):
    _name = 'product.product'
    _inherit = [
        'product.product',
        'disable.followers',
    ]
    _followers_key = 'product_followers'


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = [
        'product.template',
        'disable.followers',
    ]
    _followers_key = 'product_followers'


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = [
        'stock.picking',
        'disable.followers',
    ]
    _followers_key = 'product_followers'


class Lot(models.Model):
    _name = 'stock.production.lot'
    _inherit = [
        'stock.production.lot',
        'disable.followers',
    ]
    _followers_key = 'product_followers'
