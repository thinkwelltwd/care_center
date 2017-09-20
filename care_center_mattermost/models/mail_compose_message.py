from odoo import api, fields, models


class MailComposer(models.TransientModel):

    _inherit = 'mail.compose.message'

    @api.onchange('template_id')
    def set_partner_ids_domain(self):
        template = self.template_id.sudo()
        default_partner_domain = {
            'domain': {
                'partner_ids': ([]),
            }
        }

        if not template:
            return default_partner_domain

        if not template.mail_server_id:
            return default_partner_domain

        if template.mail_server_id.server_type == 'mattermost':
            self.notify_followers = False
            self.partner_ids = False

        return {
            'domain': {
                'partner_ids': ([
                    ('mm_accesstoken', '!=', False),
                    ('user_ids', '!=', self.env.uid),
                ]),
            }
        }
