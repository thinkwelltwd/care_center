from datetime import datetime, timedelta
from odoo.fields import Datetime
from odoo.tests import common
from odoo.tools import float_round


class TestTimesheetTimer(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestTimesheetTimer, cls).setUpClass()

        User = cls.env['res.users'].with_context({'no_reset_password': True})
        Factor = cls.env['hr_timesheet_invoice.factor']
        Task = cls.env['project.task']
        Timesheet = cls.env['account.analytic.line']
        Project = cls.env['project.project']

        user_group_employee = cls.env.ref('base.group_user')
        user_group_project_user = cls.env.ref('project.group_project_user')

        cls.user_projectuser = User.create({
            'name': 'Armande ProjectUser',
            'login': 'Armande',
            'email': 'armande.projectuser@example.com',
            'groups_id': [(6, 0, [user_group_employee.id, user_group_project_user.id])]
        })

        cls.no_discount = Factor.create({
            'name': 'No Discount',
            'factor': 0.0,
        })

        cls.full_discount = Factor.create({
            'name': 'Full Discount',
            'factor': 100.0,
        })

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always'})

        cls.api_project = Project.create({
            'name': 'Timed Project',
            'partner_id': cls.partner_1.id,
        })

        cls.task = Task.create({
            'name': 'Bill for this work',
            'partner_id': cls.partner_1.id,
            'project_id': cls.api_project.id,
        })

        # timesheet with 15 minutes on previous Start/Pause instance
        # and 15 minutes on the current instance
        Timesheet.create({
            'name': 'Worked on this briefly',
            'date_start': Datetime.to_string(datetime.now() - timedelta(minutes=15)),
            'user_id': cls.user_projectuser.id,
            'task_id': cls.task.id,
            'project_id': cls.api_project.id,
            'factor': cls.no_discount.id,
            'timer_status': 'stopped',
            'amount': 40,
            'full_duration': .25,
            'unit_amount': .25,
        })

    def test_minimum_duration(self):

        Timer = self.env['timesheet_timer.wizard']
        Param = self.env['ir.config_parameter']

        minimum_minutes = 60.0
        Param.set_param(
            'start_stop.minimum_work_log', minimum_minutes,
            groups=['base.group_system'],
        )

        ts = self.task.timesheet_ids[0]
        timer = Timer.create({
            'completed_timesheets': 0,
            'timesheet_id': ts.id,
            'factor': ts.factor.id,
        })

        # Under minimum returns minimum duration
        stats = timer.timesheet_stats()
        self.assertEqual(stats['unit_amount'], minimum_minutes / 60.0)

        minimum_minutes = 15.0
        Param.set_param(
            'start_stop.minimum_work_log', minimum_minutes,
            groups=['base.group_system'],
        )

        # Over minimum returns timed duration
        stats = timer.timesheet_stats()
        self.assertAlmostEqual(float_round(stats['unit_amount'], 1), .5)
