from odoo import api, models


class MailInvite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        result['send_mail'] = False
        return result
