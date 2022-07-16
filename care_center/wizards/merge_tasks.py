import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def related_tasks(task1, task2):
    if task1.partner_id == task2.partner_id:
        return True

    t1_parent = task1.partner_id.parent_id
    t2_parent = task2.partner_id.parent_id

    if not all([t1_parent, t2_parent]):
        return False

    return t1_parent and t1_parent == task2.partner_id


class MergeTasks(models.TransientModel):
    _name = 'merge.task.wizard'
    _description = 'Merge Tasks'

    task_ids = fields.Many2many(
        'project.task',
        string='Tasks',
        default=lambda self: self.env.context.get('active_ids'),
    )
    dst_task_id = fields.Many2one('project.task', string='Destination Task', required=True)

    def action_merge(self):

        self.merge_validation()
        self.merge_name_description()
        self.transfer_messages()
        self.transfer_time()
        self.transfer_tags()
        self.close_old_tasks()

        return True

    def merge_validation(self):

        for task in self.task_ids:
            if task.id == self.dst_task_id.id or not task.timesheet_ids:
                continue

            if not related_tasks(task, self.dst_task_id):
                tp = task.partner_id.name if task.partner_id else 'N/A'
                dst_tp = self.dst_task_id.partner_id.name if self.dst_task_id.partner_id else 'N/A'
                raise UserError(
                    _(
                        'Cannot merge tasks! Tasks with timesheets cannot change partners.\n\n'
                        'Task "%s" has timesheets and partner "%s" is not related to destination '
                        'task partner "%s".' % (task.name, tp, dst_tp)
                    )
                )

    def merge_name_description(self):

        names = [self.dst_task_id.name]
        descriptions = [self.dst_task_id.description]

        for task in self.task_ids:
            if task.id == self.dst_task_id.id:
                continue

            for name in task:
                names.append(name.name)
                descriptions.append(name.description)

        self.dst_task_id.write({
            'name': ', '.join([str(name) for name in names]),
            'description': ', '.join([str(desc) for desc in descriptions]),
        })

    def transfer_messages(self):
        for task in self.task_ids:
            for message in task.message_ids:
                message.res_id = self.dst_task_id.id

    def transfer_time(self):
        planned_hours = self.dst_task_id.planned_hours

        for task in self.task_ids:
            if task.id == self.dst_task_id.id:
                continue

            planned_hours += task.planned_hours
            for timesheet in task.timesheet_ids:
                timesheet.task_id = self.dst_task_id.id

        self.dst_task_id.planned_hours = planned_hours

    def transfer_tags(self):
        for task in self.task_ids:
            if task.id == self.dst_task_id.id:
                continue

            for tag in task.tag_ids:
                tag.write({'tag_ids': (6, 0, [self.dst_task_id.id])})

    def close_old_tasks(self):
        """
        Write the link to every task so users can see the task was merged
        Deactivate the old tasks
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dst_task = self.dst_task_id.id

        for task in self.task_ids:
            if task.id == self.dst_task_id.id:
                continue

            # post the link to every task so users can see the task was merged
            url = '%s/web#id=%s&amp;view_type=form&amp;model=project.task' % (base_url, dst_task)
            task.message_post(body="This task has been merged into: %s" % url)

        self.task_ids.active = False
        self.dst_task_id.active = True
