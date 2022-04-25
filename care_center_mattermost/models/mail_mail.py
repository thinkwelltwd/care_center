from html2text import html2text
import logging
from odoo import api, models, _

logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def send_chat(self, mail):

        MattermostServer = mail.mail_server_id

        if mail.model:
            model = self.env['ir.model'].sudo().search([('model', '=', mail.model)])[0]
        else:
            model = None
        if model:
            mail = mail.with_context(model_name=model.name)

        message = html2text(mail.body).strip()

        for recipient in mail.recipient_ids:
            if not recipient.user_id.mm_accesstoken:
                logging.error('Cannot send message. %s has no access token.' % recipient)
                continue

            MattermostServer.send_msg(
                sender=mail.author_id,
                recipient=recipient.email,
                message=message,
            )

        mail.write({'state': 'sent'})

    def send(self, auto_commit=False, raise_exception=False):

        for mail in self:
            if mail.mail_server_id and mail.mail_server_id.server_type == 'mattermost':
                return self.send_chat(mail=mail)

            return super(MailMail, self).send(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
            )
