from odoo import models, api


class CareCenterBase(models.AbstractModel):
    """
    Base model including helper functions / fields
    useful in multiple other project models.
    """
    _name = 'care_center.base'
    _description = 'Care Center Base'

    @api.multi
    def get_partner_ids(self, field=None):
        """
        partner_id can be a Company or Contact on a company.
        When the Company ID changes, it's helpful to change domains
        on Calls / Tickets / Tasks, so return ID of Company and all
        contact_ids of the company.
        """
        if field is None:
            field = self.partner_id

        parent = field.commercial_partner_id
        partner_ids = parent.child_ids.mapped('id')
        partner_ids.append(parent.id)

        return partner_ids

    @api.multi
    def get_partner_domain(self, partner_ids=()):
        if not partner_ids:
            partner_ids = self.get_partner_ids()

        return [
            '|',
            self.get_catchall_domain(),
            ('partner_id', 'in', partner_ids),
        ]

    @api.model
    def get_catchall_domain(self):
        """This is a hook to be overridden in subclasses"""
        return ('partner_id', '=', False)

    @api.multi
    def mailserver_mode(self):
        """
        Model is being created / modified from mailserver cron job.
        In such cases, relax validation checks to permit the record
        to be created. Users can refine / correct later.
        """
        return 'fetchmail_cron_running' in self.env.context
