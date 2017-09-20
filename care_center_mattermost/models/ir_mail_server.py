from ..mattermost import Client
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    server_type = fields.Selection([
        ('email', 'Email'),
        ('mattermost', 'Mattermost')
        ],
        string='Server Type', required=True, default='email',
    )

    def get_scheme(self):
        if self.smtp_encryption == 'none':
            return 'http'
        return 'https'

    def test_mattermost_conection(self):

        try:
            home_page = requests.get(
                '%s://%s:%s' % (self.get_scheme(), self.smtp_host, self.smtp_port),
                timeout=.5, verify=False
            )
        except requests.exceptions.ConnectTimeout:
            raise UserError('Unable to connect to %s' % self.smtp_host)

        if home_page and 'mattermost' not in home_page.text.lower():
            raise UserError('Connection successful, but does not appear to be a Mattermost Server.')

        raise UserError(_("Mattermost Server is reachable!"))

    @api.multi
    def test_smtp_connection(self):
        if self.server_type == 'mattermost':
            self.test_mattermost_conection()
        return super(IrMailServer, self).test_smtp_connection()


    def send_msg(self, sender, recipient, message):
        """
        Send Mattermost Message

        :param sender: Sending user's res.partner instance
        :param recipient: Recipient's email address
        :param message: mail.mail instance
        """
        url = '%s://%s' % (self.get_scheme(), self.smtp_host)

        mattermost = Client(url=url, port=self.smtp_port, token=sender.mm_accesstoken)

        mattermost.send_message(
            sender=sender.email,
            recipient=recipient,
            message=message,
        )

