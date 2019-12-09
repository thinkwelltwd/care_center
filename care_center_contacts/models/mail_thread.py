from odoo import models


class MailThread(models.AbstractModel):
    _name = 'mail.thread'
    _inherit = 'mail.thread'

    def _search_on_partner(self, email_address, extra_domain=[]):
        """
        Search for partner with this email address, preferring
        full-fledged Odoo contact.
        """
        partner_id = super()._search_on_partner(email_address, extra_domain=extra_domain)

        if not partner_id:
            Email = self.env['extra.contactinfo'].sudo()
            email = Email.search([
                ('name', '=', email_address),
                ('type', '=', 'email'),
            ], limit=1)

            try:
                partner_id = email.partner_id.id
            except Exception:
                pass

        return partner_id
