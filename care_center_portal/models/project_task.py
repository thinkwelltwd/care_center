from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _handle_task_post(self, context, partner):
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
            return self.handle_create(partner, values)
        return self.handle_update()

    def handle_create(self, partner, values):
        values['user_id'] = False
        values['company_id'] = partner.company_id.id
        values['project_id'] = int(values['project_id'])
        return self.create(values)

    def handle_update(self):
        pass
