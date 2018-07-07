from odoo.exceptions import ValidationError
from odoo.tests import common


class TestTask(common.TransactionCase):

    def setUp(self):
        super(TestTask, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always',
        })

        self.api_project = self.env['project.project'].create({
            'name': 'API Project',
            'partner_id': self.partner_1.id,
        })

    def test_child_tasks_must_be_closed(self):

        Task = self.env['project.task']

        task = Task.create({
            'name': 'Hard work ahead',
            'project_id': self.api_project.id,
            'description': 'This is a BIG new Task!',
        })

        Task.create({
            'parent_task_id': task.id,
            'name': 'Broke into smaller pieces',
            'project_id': self.api_project.id,
            'description': 'This is a smaller sub Task!',
        })

        with self.assertRaises(ValidationError):
            task.toggle_active()
