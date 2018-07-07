from odoo.tests import common


class TestTask(common.TransactionCase):

    def setUp(self):
        super(TestTask, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always'})

        self.api_project = self.env['project.project'].create({
            'name': 'Wrong Project',
            'partner_id': self.partner_1.id,
        })

    def test_task_converts_to_opportunity(self):

        Task = self.env['project.task']
        msg = 'This Task should have been an opportunity'

        task = Task.create({
            'name': 'Good Sales Lead',
            'project_id': self.api_project.id,
            'description': msg,
        })
        phone = self.env['crm.phonecall'].create({
            'task_id': task.id,
            'name': 'Sales Call',
        })

        res = task.convert_to_opportunity()
        self.assertFalse(task.active)

        lead = self.env['crm.lead'].browse(res['res_id'])

        self.assertEqual(task.description, lead.description)
        self.assertEqual(task.partner_id, lead.partner_id)

        self.assertFalse(phone.task_id)
        self.assertEqual(phone.opportunity_id, lead)
