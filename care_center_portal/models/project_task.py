from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _handle_task_post(self, context, partner, mode='create'):
        values = {
            key: context.get(key)
            for key in (
                'project_id',
                'name',
                'partner_id',
                'description',
            )
        }
        if not self:
            return self.handle_create(values)
        return self.handle_update()

    def handle_create(self, values):
        self.handle_project(values)
        values['user_id'] = False
        return self.create(values)

    def handle_update(self):
        pass

    def handle_project(self, values):
        project_id = values.get('project_id', 0)
        if project_id:
            values['project_id'] = int(project_id)
            team = self.env['project.project'].sudo().browse(values['project_id']).mapped('team_id')
            values['team_id'] = team.id
