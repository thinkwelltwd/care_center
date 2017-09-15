# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def create(self, vals):
        project = super(ProjectProject, self).create(vals)

        Param = self.env['ir.config_parameter']
        email_prefix = Param.get_param('mail.catchall.alias', '').lower()
        name_prefix = Param.get_param('care_center.alias_name_prefix', '')

        if name_prefix == 'True':
            if not project.alias_name.startswith(email_prefix):
                project.write({'alias_name': '%s+%s' % (email_prefix, project.alias_name)})

        return project


class ProjectConfiguration(models.TransientModel):
    _inherit = 'project.config.settings'

    alias_name_prefix = fields.Boolean(
        string='Alias Name Prefix',
        default=True,
        help='Prepend catchall email alias as prefix to project alias name. \n'
             'i.e. support+project-name',
    )

    @api.multi
    def set_alias_name_prefix(self):
        self.env['ir.config_parameter'].set_param(
            'care_center.alias_name_prefix', self.alias_name_prefix,
            groups=['base.group_system'],
        )

    @api.model
    def default_get(self, fields):
        res = super(ProjectConfiguration, self).default_get(fields)
        Param = self.env['ir.config_parameter']
        name_prefix = Param.get_param('care_center.alias_name_prefix', '')

        res.update({
            'alias_name_prefix': True if name_prefix == 'True' else False,
        })
        return res
