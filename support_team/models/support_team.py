from odoo import api, fields, models


class SupportTeam(models.Model):
    _inherit = 'crm.team'

    type_team = fields.Selection(
        selection=[
            ('sale', 'Sale'),
            ('project', 'Project'),
            ('support', 'Support'),
        ],
        string="Type",
        default="support",
    )

    member_ids = fields.Many2many(
        'res.users',
        'team_member_user_rel',
        'team_id',
        'user_id',
        string='Team Members',
    )
