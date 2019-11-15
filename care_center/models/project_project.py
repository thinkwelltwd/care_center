from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def create(self, vals):
        project = super(ProjectProject, self).create(vals)

        Param = self.env['ir.config_parameter'].sudo()
        email_prefix = Param.get_param('mail.catchall.alias', '').lower()
        name_prefix = Param.get_param('care_center.alias_name_prefix', '')

        if name_prefix == 'True':
            if not project.alias_name.startswith(email_prefix):
                project.write({'alias_name': '%s+%s' % (email_prefix, project.alias_name)})

        return project
