from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alias_name_prefix = fields.Boolean(
        string='Alias Name Prefix',
        default=False,
        config_parameter='care_center.alias_name_prefix',
        help='Prepend catchall email alias as prefix to project alias name. \n'
             'i.e. support+project-name',
    )
