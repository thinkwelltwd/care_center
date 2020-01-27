from odoo import api, fields, models, modules, _
from odoo.exceptions import UserError
from odoo.tools import date_utils


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

    @api.multi
    def get_hr_timesheet_id(self, company_id):
        """
        Always return HR Timesheet if one exists for the current Employee and Time period

        If no HR Timesheet exists, and manage_hr_timesheet is True, create it.
        """
        self.ensure_one()

        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.id),
        ], limit=1)
        if not employee:
            raise UserError('%s is not linked to an Employee Record' % self.env.user.name)

        Param = self.env['ir.config_parameter'].sudo()
        manage_hr_time = Param.get_param('hr_timesheet.manage_hr_timesheet', default=True)

        today = fields.Date.context_today(self)
        TimesheetSheet = self.env['hr_timesheet.sheet'].sudo()
        ts = TimesheetSheet.search(
            [
                ('employee_id', '=', employee.id),
                ('date_start', '<=', today),
                ('date_end', '>=', today),
                ('company_id', '=', company_id),
            ],
            limit=1,
        ).mapped('id')
        if ts:
            return ts[0]

        if not manage_hr_time:
            return False

        return TimesheetSheet.with_context(company_id=company_id).create({
            'employee_id': employee.id,
            'company_id': company_id,
        }).id
