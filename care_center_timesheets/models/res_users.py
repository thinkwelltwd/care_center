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

        my_tasks_sql = """
            SELECT COUNT(*) FROM project_task
            WHERE active = True
            AND (user_id = %(user_id)s OR id IN (
                    SELECT DISTINCT(task_id) 
                    FROM account_analytic_line 
                    WHERE user_id = %(user_id)s
                    AND task_id IS NOT NULL
                 )
            )
        """
        self.env.cr.execute(my_tasks_sql, {'user_id': self.env.uid})
        my_tasks = self.env.cr.dictfetchall()

        if my_tasks:

            my_timers_sql = """
                SELECT DISTINCT(task_id), timer_status, project_task.name
                FROM account_analytic_line
                INNER JOIN project_task
                ON account_analytic_line.task_id=project_task.id
                WHERE 
                    account_analytic_line.user_id = %s AND
                    account_analytic_line.task_id IN (
                        SELECT id FROM project_task 
                        WHERE active = True 
                        AND stage_id IN (SELECT id FROM project_task_type WHERE fold=False)
                    );
            """

            self.env.cr.execute(my_timers_sql, [self.env.uid])
            task_timer_data = self.env.cr.dictfetchall()
            task_id, task_name = None, None
            unique_ids = set()

            for task in task_timer_data:
                unique_ids.add(task['task_id'])
                if task['timer_status'] == 'running':
                    task_id = task['task_id']
                    task_name = task['name']
                    break

            timer_systray = {
                'type': 'timer',
                'active_task_id': task_id,
                'active_task_name': task_name,
                'my_timers': len(unique_ids),
                'my_tasks': my_tasks[0]['count'],
                'name': _("My Tasks or Followed Tasks"),
                'model': 'project.task',
                'icon': modules.module.get_module_icon('care_center'),
            }
            res.insert(self._get_systray_index(res), timer_systray)

        return res
