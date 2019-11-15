from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alias_name_prefix = fields.Boolean(
        string='Alias Name Prefix',
        default=True,
        config_parameter='care_center.alias_name_prefix',
        help='Prepend catchall email alias as prefix to project alias name. \n'
             'i.e. support+project-name',
    )
