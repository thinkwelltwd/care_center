# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    support_team_id = fields.Many2one(
        'support.team', 'Support Team',
        help='If set, support team used for Issues & Tasks related to this partner'
    )
