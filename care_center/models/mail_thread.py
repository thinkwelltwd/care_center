import email
from email.message import Message

from odoo import models, api, _
import logging
_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def get_prefix(self, model):
        try:
            prefix = self.env['ir.sequence'].search([('code', '=', model)])[0].prefix
            return prefix[:prefix.index('%')]
        except IndexError:
            return ''

    def extract_code(self, prefix, subject):
        """
        Extract Code from Subject string.
        Code should not contain spaces and should begin
        with some standard string prefix such as "TKT/"
        """
        subject = subject.split()
        for word in subject:
            if word.startswith(prefix):
                return word

    def get_task_id(self, subject):
        """Get Model ID by looking up code from subject line"""
        code_prefix = self.get_prefix(model='project.task')
        if not code_prefix:
            return None

        code = self.extract_code(code_prefix, subject)
        if not code:
            return None

        try:
            task = self.env['project.task'].search([('code', '=', code)])
            return task and task.id
        except ValueError:
            return None

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        """
        Some email clients strip out the Message-ID header :-(

        When thread_id is None, try to extract the Task Code from the subject line
        to increase chance that incoming emails will be attached to existing Task.
        """
        msg = message

        if not thread_id and model == 'project.task':
            if not isinstance(msg, Message):
                if isinstance(msg, str):
                    # Warning: message_from_string doesn't always work correctly on unicode,
                    # we must use utf-8 strings here :-(
                    msg = message.encode('utf-8')
                msg = email.message_from_string(msg)

            thread_id = self.get_task_id(subject=msg['subject'])
            if thread_id:
                _logger.info('Found %s thread_id %s for %s' % (model, thread_id, msg['subject']))

        return super(MailThread, self).message_process(
            model=model, message=message, custom_values=custom_values,
            save_original=save_original, strip_attachments=strip_attachments,
            thread_id=thread_id,
        )
