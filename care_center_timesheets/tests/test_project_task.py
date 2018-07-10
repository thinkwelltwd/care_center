# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import UserError, ValidationError


class TestTask(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestTask, cls).setUpClass()

        User = cls.env['res.users'].with_context({'no_reset_password': True})
        Factor = cls.env['hr_timesheet_invoice.factor']
        Task = cls.env['project.task']
        Stage = cls.env['project.task.type']
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

        cls.stage_done = Stage.create({
            'name': 'Done',
            'is_invoiceable': True,
        })

        cls.stage_wip = Stage.create({
            'name': 'In Progress',
            'is_invoiceable': False,
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
            'stage_id': cls.stage_wip.id,
            'planned_hours': 75,
        })

        cls.task.write({
            'timesheet_ids': [
                (0, 0, {
                    'name': 'Worked on this briefly',
                    'user_id': cls.user_projectuser.id,
                    'project_id': cls.api_project.id,
                    'factor': cls.no_discount.id,
                    'timer_status': 'stopped',
                    'amount': 40,
                    'full_duration': .5,
                    'unit_amount': .5,
                }),
                (0, 0, {
                    'name': 'Go down deep; stay down long',
                    'user_id': cls.user_projectuser.id,
                    'project_id': cls.api_project.id,
                    'factor': cls.no_discount.id,
                    'timer_status': 'stopped',
                    'amount': 40,
                    'full_duration': 4.5,
                    'unit_amount': 4.5,
                }),
            ]
        })

    def test_check_invoiceable_stage(self):
        with self.assertRaises(UserError):
            self.task.check_invoiceable_stage()

        self.task.write({'stage_id': self.stage_done.id})
        self.task.check_invoiceable_stage()

    def test_mark_timesheets_ready(self):

        for ts in self.task.timesheet_ids:
            self.assertFalse(ts.timesheet_ready_to_invoice)

        self.task.write({'stage_id': self.stage_done.id})
        self.task.mark_timesheets_ready()

        worked_hours = 0
        for ts in self.task.timesheet_ids:
            worked_hours += ts.unit_amount
            self.assertTrue(ts.timesheet_ready_to_invoice)

        self.assertEqual(worked_hours, self.task.effective_hours)

    def test_timesheet_compute_durations(self):

        for ts in self.task.timesheet_ids:
            ts._compute_durations()
            hours = ts.full_duration
            hours -= (hours * ts.factor.factor / 100.0)
            self.assertEqual(ts.unit_amount, hours)


    def test_timesheet_check_if_marked_ready(self):

        for ts in self.task.timesheet_ids:
            self.assertFalse(ts.timesheet_ready_to_invoice)

        self.task.write({'stage_id': self.stage_done.id})
        self.task.mark_timesheets_ready()

        # now we shouldn't be able to create another time sheet on this task
        with self.assertRaises(ValidationError):
            self.env['account.analytic.line'].create({
                'name': 'Ooops. Ned to add more time',
                'user_id': self.user_projectuser.id,
                'task_id': self.task.id,
                'project_id': self.api_project.id,
                'factor': self.no_discount.id,
                'amount': 40,
                'full_duration': 4.5,
                'unit_amount': 4.5,
            })

    def test_timer_buttons(self):

        ts_count = len(self.task.timesheet_ids)
        self.task.timer_start()
        self.assertEqual(len(self.task.timesheet_ids), ts_count + 1)
        timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', self.task.id),
            ('timer_status', '=', 'running'),
        ], limit=1)

        with self.assertRaises(UserError):
            self.task.timer_start()

        self.task.timer_pause()
        paused = self.task.timesheet_ids.filtered(lambda ts: ts.timer_status == 'paused')
        self.assertEqual(len(paused), 1)

        self.task.timer_start()
        self.task.timer_stop()

        timer = self.env['timesheet_timer.wizard'].search_count([
            ('timesheet_id', '=', timesheet.id)
        ])

        self.assertEqual(timer, 1)

    def test_add_planned_expected_difference(self):

        ts_count = len(self.task.timesheet_ids)
        ts_total_time = sum(ts.unit_amount for ts in self.task.timesheet_ids)
        self.assertGreater(self.task.planned_hours, ts_total_time)

        # when task is not invoiceable, no timesheets should be created
        self.task.write({'is_invoiceable': 'no'})
        self.task.add_planned_expected_difference()
        self.assertEqual(ts_count, len(self.task.timesheet_ids))

        self.task.write({'is_invoiceable': 'yes'})
        self.task.add_planned_expected_difference()
        self.assertEqual(ts_count + 1, len(self.task.timesheet_ids))

        ts_total_time = sum(ts.unit_amount for ts in self.task.timesheet_ids)
        self.assertAlmostEqual(ts_total_time, self.task.planned_hours)
