from odoo import models, fields


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'project.tag.team.base']

    team_id = fields.Many2one(
        'crm.team',
        string="Project Team",
        domain=[
            ('type_team', 'in', ('support', 'project')),
        ],
    )
