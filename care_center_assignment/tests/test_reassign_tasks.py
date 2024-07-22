from odoo.tests import common


class TestReassignTask(common.TransactionCase):
    """
        Testing the Reassign Tasks Wizard.
        Currently this test succeeds, however I had to remove the required=True
        from the field var_ticket_communication_mode.
    """

    def setUp(self):
        super(TestReassignTask, self).setUp()

        Partner = self.env['res.partner']
        self.partner1 = Partner.create({
            'name': 'Bob Smith',
            'email': 'bobsmith@testing.com',
        })

        self.partner2 = Partner.create({
            'name': 'Joe Tester',
            'email': 'joetester@testing.com',
        })

        Users = self.env['res.users'].with_context(skip_default_tasks=True)
        self.user1 = Users.create({
            'partner_id': self.partner1.id,
            'login': self.partner1.email,
        })

        self.user2 = Users.create({
            'partner_id': self.partner2.id,
            'login': self.partner2.email,
        })

        self.api_project = self.env['project.project'].create({
            'name': 'API Project',
            'partner_id': self.partner1.id,
        })

        Task = self.env['project.task']
        self.task1 = Task.create({
            'name': 'Big Task 1',
            'project_id': self.api_project.id,
            'description': 'This is a BIG new Task!',
            'user_ids': [(4, self.user1.id)],
        })

        self.subtask1 = Task.create({
            'parent_id': self.task1.id,
            'name': 'Broke into smaller pieces',
            'project_id': self.api_project.id,
            'description': 'This is a smaller sub Task!',
            'user_ids': [(4, self.user1.id)],
        })

        self.task2 = Task.create({
            'name': 'Big Task 2',
            'project_id': self.api_project.id,
            'description': 'Test task number 2',
            'user_ids': [(4, self.user1.id)],
        })

        self.subtask2 = Task.create({
            'parent_id': self.task2.id,
            'name': 'Subtask of test 2',
            'project_id': self.api_project.id,
            'description': 'This is a smaller sub Task!',
            'user_ids': [(4, self.user1.id)],
        })

    def test_reassign_tasks(self):
        ReassignTasks = self.env['reassign_tasks.wizard']
        task_ids = [self.task1.id, self.task2.id]
        reassign = ReassignTasks.create({
            'name': 'Test Reassigns',
            'reassign_to': 'user',
            'assigned_to': self.user2.id,
            'task_ids': [(6, 0, task_ids)],
        })

        reassign.reassign_tasks()

        self.assertEqual(self.task1.user_ids[0].id, self.user2.id, 'Reassigning Task 1 failed')
        self.assertEqual(self.task2.user_ids[0].id, self.user2.id, 'Reassigning Task 2 failed')
        self.assertEqual(
            self.subtask1.user_ids[0].id, self.user2.id, 'Reassigning Subtask 1 failed'
        )
        self.assertEqual(
            self.subtask2.user_ids[0].id, self.user2.id, 'Reassigning Subtask 2 failed'
        )
        print('Reassign Tasks succeeded.')
