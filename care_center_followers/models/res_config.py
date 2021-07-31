from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_followers = fields.Boolean(
        string='Disable auto-creating followers on Accounting records',
        default=False,
        config_parameter='care_center_followers.account_followers',
    )

    sale_followers = fields.Boolean(
        string='Disable auto-creating followers on Sale records',
        default=False,
        config_parameter='care_center_followers.sale_followers',
    )

    product_followers = fields.Boolean(
        string='Disable auto-creating followers on Product / Inventory records',
        default=False,
        config_parameter='care_center_followers.product_followers',
    )
