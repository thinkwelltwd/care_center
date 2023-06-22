from distutils.util import strtobool

from odoo import models


class MailThread(models.AbstractModel):
    """
    Base model to disable auto-subscribing followers
    """
    _name = 'mail.thread'
    _inherit = 'mail.thread'

    def message_subscribe(self, *args, **kwargs):
        """
        Override this method, so that followers are disabled when calling
        various action methods on an existing record.
        """
        if self.env.context.get('disable_auto_subscribe', False):
            return True
        return super().message_subscribe(*args, **kwargs)

    def _message_auto_subscribe(self, *args, **kwargs):
        if self.env.context.get('disable_auto_subscribe', False):
            return True
        return super()._message_auto_subscribe(*args, **kwargs)

    def _message_auto_subscribe_followers(self, *args, **kwargs):
        """
        Override this method, so that followers are disabled when creating new records.
        """
        if self.env.context.get('disable_auto_subscribe', False):
            return []
        return super()._message_auto_subscribe_followers(*args, **kwargs)


class DisableFollowers(models.AbstractModel):
    """
    Base model to disable auto-subscribing followers
    """
    _name = 'disable.followers'
    _description = 'Disable Followers'
    _followers_key = ''

    def auto_followers_context(self):
        """
        Set context key to disable / enable auto-subscribing followers on this model.
        """
        Param = self.env['ir.config_parameter'].sudo()
        disable_subscribe = Param.get_param(f'care_center_followers.{self._followers_key}', 'False')
        return {'disable_auto_subscribe': strtobool(disable_subscribe)}

    def create(self, vals):
        context = self.auto_followers_context()
        self = self.with_context(**context)
        if self.env.context.get('disable_auto_subscribe', False):
            for record in vals:
                record.pop('message_follower_ids', None)
        return super().create(vals)
