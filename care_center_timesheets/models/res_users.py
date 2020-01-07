from odoo import api, fields, models, modules, _


class ResUsers(models.Model):
    _inherit = "res.users"

    previous_running_timesheet = fields.Many2one(
        'account.analytic.line',
        string='Previous Running Timesheet',
    )

    @api.multi
    def get_active_timesheet(self):
        """
        Return the active timesheet of this user
        """
        self.ensure_one()
        AccountAnalyticLine = self.env['account.analytic.line'].sudo()
        return AccountAnalyticLine.search(
            [
                ('timer_status', '=', 'running'),
                ('user_id', '=', self.id),
            ],
            limit=1,
        )

    def _get_systray_index(self, res):
        """
        Timers should be at the top, or after meetings if meetings are found
        """
        if not res or res[0]['type'] != 'meeting':
            return 0
        return 1

    @api.model
    def systray_get_activities(self):
        res = super(ResUsers, self).systray_get_activities()

        Task = self.env['project.task'].sudo()
        my_tasks = Task.search_count([
            '|',
            ('timesheet_ids.user_id', '=', self.env.uid),
            ('user_id', '=', self.env.uid),
        ])

        if my_tasks:

            my_timers = Task.search_count([
                ('stage_id.fold', '=', False),
                ('timesheet_ids.user_id', '=', self.env.uid),
            ])

            AccountAnalyticLine = self.env['account.analytic.line'].sudo()
            active_task = AccountAnalyticLine.search_read(
                [
                    ('timer_status', '=', 'running'),
                    ('user_id', '=', self.env.uid),
                ],
                ['task_id']
            )
            if active_task:
                task_id, name = active_task[0]['task_id']
            else:
                task_id, name = None, None

            timer_systray = {
                'type': 'timer',
                'active_task_id': task_id,
                'active_task_name': name,
                'my_timers': my_timers,
                'my_tasks': my_tasks,
                'name': _("My Tasks or Followed Tasks"),
                'model': 'project.task',
                'icon': modules.module.get_module_icon('care_center'),
            }
            res.insert(self._get_systray_index(res), timer_systray)

        return res
