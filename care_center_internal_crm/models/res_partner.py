from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_odoo_user(self):
        """
        Quick way to get Odoo res.user record for a res.partner,
        useful for getting internal call partner.
        """
        return self.env['res.users'].search([
            ('partner_id', '=', self.id),
        ])
