from odoo import models, api


class CareCenterBase(models.AbstractModel):
    """
    Base model including helper functions / fields
    useful in multiple other project models.
    """
    _name = 'care_center.base'

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
        partner_ids = [
            field.commercial_partner_id.id
        ] + field.commercial_partner_id.child_ids.ids
        # Need to search by parent_id or else tickets from inactive
        # partners will be skipped
        return self.env['res.partner'].search([
            ('parent_id', 'in', partner_ids),
        ]).ids

    @api.multi
    def get_partner_domain(self, partner_ids=()):
        if not partner_ids:
            partner_ids = self.get_partner_ids()

        return [
            '|',
            ('partner_id', '=', False),
            ('partner_id', 'in', partner_ids),
        ]
