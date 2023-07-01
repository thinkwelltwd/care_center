from odoo import models


class MailThread(models.AbstractModel):
    _name = 'mail.thread'
    _inherit = 'mail.thread'

    def _mail_search_on_partner(self, email_addresses, extra_domain=None):
        """
        Search for partner with this email address, preferring
        full-fledged Odoo contact.
        """
        if isinstance(email_addresses, str):
            email_addresses = [email_addresses]
        partners = super()._mail_search_on_partner(email_addresses, extra_domain=extra_domain or [])

        if not partners:
            partners = self.env['res.partner'].search([
                ('contact_info_ids.name', 'in', email_addresses),
                ('contact_info_ids.type', '=', 'email'),
             ])

        return partners
