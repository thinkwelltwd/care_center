from odoo import api, fields, models


class ReassignTasksWizard(models.TransientModel):
    _inherit = 'reassign_task.wizard'
    _name = 'reassign_tasks.wizard'
    _description = 'Reassign Tasks to User or Team'

    task_ids = fields.Many2many(
        'project.task',
        string='Tasks',
        default=lambda self: self.env.context.get('active_ids'),
        required=True,
    )

    def reassign_tasks(self):
        for task_id in self.task_ids:
            if not self.verify_assignment_changes(task_id):
                continue

            team_id = self.team_id and self.team_id.id
            assigned_to = self.assigned_to and self.assigned_to.id
            assignment = self.env['task.assignment'].create({
                'name': self.name,
                'description': self.description,
                'assigned_by': self.env.uid,
                'assigned_to': assigned_to,
                'team_id': team_id,
                'task_id': task_id.id,
            })

            if assigned_to:
                user_ids = [(6, 0, [assigned_to])]
            else:
                user_ids = [(5, 0, 0)]

            stats = {
                'user_ids': user_ids,
            }
            if self.team_id:
                stats['team_id'] = self.team_id.id

            if self.reassign_subtasks:
                for subtask in task_id._get_all_subtasks():
                    subtask.with_context({'tracking_disable': True}).write(stats)

            stats['assignment_ids'] = [(4, assignment.id, None)]
            task_id.with_context({'tracking_disable': True}).write(stats)

            if self.send_notifications:
                task_id.message_post(
                    body=self.get_body(),
                    subject=self.get_subject(),
                    message_type='email',
                    parent_id=False,
                    attachments=None,
                    content_subtype='html',
                    partner_ids=self.get_partner_ids(),
                )

            self.notify_partner_email()
            if self.assigned_to:
                task_id.message_subscribe([self.assigned_to.partner_id.id])

    def verify_assignment_changes(self, task):
        if self.assigned_to:
            if self.assigned_to in task.user_ids:
                if self.team_id:
                    if self.team_id != task.team_id:
                        return True
                return False
        if self.team_id:
            if self.team_id == task.team_id:
                return False
        return True

    @api.onchange('assigned_to', 'team_id')
    def prefill_description(self):
        if not self.name:
            self.name = 'Initial Assignment'
