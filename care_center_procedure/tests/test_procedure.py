from odoo.exceptions import ValidationError
from odoo.tests import common


class TestProcedure(common.TransactionCase):

    def setUp(self):
        super(TestProcedure, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always',
        })

        self.api_project = self.env['project.project'].create({
            'name': 'API Project',
            'partner_id': self.partner_1.id,
        })

    def test_procedures_may_not_be_nested(self):
        Procedure = self.env['procedure.procedure']
        parent = Procedure.create({
            'name': 'Configure Network',
            'description': 'Configure the new network.',
        })

        child1 = Procedure.create({
            'name': 'Configure Modem',
            'description': 'Configure the modem.',
            'parent_id': parent.id,
        })

        with self.assertRaises(ValidationError):
            Procedure.create({
                'name': 'Configure Switch',
                'description': 'Configure the switch.',
                'parent_id': child1.id,
            })
