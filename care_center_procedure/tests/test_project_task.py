from odoo.tests import common


class TestTaskProcedureAssignment(common.TransactionCase):

    def setUp(self):
        super(TestTaskProcedureAssignment, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Bill Smith',
            'email': 'bill@smith.com',
            'notify_email': 'always',
        })

        self.api_project = self.env['project.project'].create({
            'name': 'API Project',
            'partner_id': self.partner_1.id,
        })

        Task = self.env['project.task']
        self.task = Task.create({
            'name': 'Hard work ahead',
            'project_id': self.api_project.id,
            'description': 'This is a BIG new Task!',
        })

        Procedure = self.env['procedure.procedure']
        self.procedure = Procedure.create({
            'name': 'Design',
            'description': 'Plan network design',
            'planned_hours': 2,
        })

        self.parent = Procedure.create({
            'name': 'Configure Network',
            'description': 'Configure the new network.',
            'planned_hours': .5,
        })

        self.child1 = Procedure.create({
            'name': 'Configure Modem',
            'description': 'Configure the modem.',
            'parent_id': self.parent.id,
        })

        self.child2 = Procedure.create({
            'name': 'Configure Switch',
            'description': 'Configure the switch.',
            'parent_id': self.parent.id,
        })

    def test_assign_procedure_increments_planned_hours(self):
        self.task.assign_procedure(self.procedure, 1)
        self.assertEqual(self.task.planned_hours, 2)

        self.task.assign_procedure(self.parent, 2)
        self.assertEqual(self.task.planned_hours, 2.5)

        assignment = self.env['procedure.assignment'].search([
            ('procedure_id', '=', self.procedure.id),
            ('task_id', '=', self.task.id),
        ])

        # Correct number of checklists created
        checklist_count = self.env['procedure.assignment'].search_count([
            ('procedure_id.parent_id', '=', self.parent.id),
            ('task_id', '=', self.task.id),
        ])
        self.assertEqual(checklist_count, 2)

        assignment.unlink()
        self.assertEqual(self.task.planned_hours, .5)
