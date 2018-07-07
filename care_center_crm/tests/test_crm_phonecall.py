from odoo.tests import common


class TestCRMPhonecall(common.TransactionCase):

    def setUp(self):
        super(TestCRMPhonecall, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always'})

        self.api_project = self.env['project.project'].create({
            'name': 'Yet another Project',
            'partner_id': self.partner_1.id,
        })

    def test_phonecall_creates_task(self):

        Phonecall = self.env['crm.phonecall']
        Task = self.env['project.task']

        call = Phonecall.create({
            'name': 'Call should become a task',
            'partner_id': self.partner_1.id,
            'project_id': self.api_project.id,
        })

        call.create_task()

        task = Task.search([
            ('name', '=', call.name)
        ], limit=1)

        self.assertEqual(call.name, task.name)
