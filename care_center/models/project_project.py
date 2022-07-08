from odoo import api, models


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'care_center.base']

    @api.model
    def related_partner_ids(self) -> set:
        """
        Hook to return all commercial_partner_id values that
        are associated with this project. Normally will only
        be the partner assigned to the project record, but
        override to extend the logic.
        """
        if self.partner_id:
            return {self.partner_id.commercial_partner_id.id, self.partner_id.id}
        return set()

    @api.model
    def get_catchall_domain(self):
        """Override superclass (care_center.base) hook."""
        return ('catchall', '=', True)

    @api.model
    def create(self, vals):
        project = super(ProjectProject, self).create(vals)

        Param = self.env['ir.config_parameter'].sudo()
        email_prefix = Param.get_param('mail.catchall.alias', '').lower()
        name_prefix = Param.get_param('care_center.alias_name_prefix', '')

        if project.alias_name and name_prefix == 'True':
            if not project.alias_name.startswith(email_prefix):
                project.alias_name = f'{email_prefix}+{project.alias_name}'

        return project
