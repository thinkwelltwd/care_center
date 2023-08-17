import json
from odoo import models, fields, api


class ProjectTags(models.Model):
    _inherit = "project.tags"

    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
        index=True,
        help='Tag can be used on Tasks assigned to this Team',
        domain=[('type_team', '!=', 'sales')],
    )


class ProjectTagTeamBase(models.AbstractModel):
    """
    Add filtering of Project Tags by Team
    """
    _name = 'project.tag.team.base'
    _description = 'Project Tag Team Base'

    tag_ids_domain = fields.Char(
        compute='_compute_tag_ids_domain',
        readonly=True,
        store=False,
    )

    @api.depends('team_id')
    def _compute_tag_ids_domain(self):
        for record in self:
            if not record.team_id:
                domain = [('team_id', '=', False)]
            else:
                domain = [
                    '|',
                    ('team_id', '=', False),
                    ('team_id', '=', record.team_id.id),
                ]
            record.tag_ids_domain = json.dumps(domain)
