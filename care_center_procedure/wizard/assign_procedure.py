# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AssignProcedureWizard(models.TransientModel):
    _name = 'assign_procedure.wizard'
    _description = 'Assign Procedure'

    procedure_id = fields.Many2one('procedure.procedure', string='Procedure',
                                   domain=[('parent_id', '=', False)])
    sequence = fields.Integer('Sequence', default=1)
    task_id = fields.Many2one('project.task', string='Task')

    @api.multi
    def assign_procedure(self):
        self.task_id.assign_procedure(
            procedure=self.procedure_id, sequence=self.sequence,
        )
        return True
