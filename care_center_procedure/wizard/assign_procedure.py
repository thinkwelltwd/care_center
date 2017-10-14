# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AssignProcedureWizard(models.TransientModel):
    _name = 'assign_procedure.wizard'
    _description = 'Assign Procedure'

    procedure_id = fields.Many2one('procedure.procedure', string='Procedure',
                                   domain=[('parent_id', '=', False)])
    sequence = fields.Integer('Sequence', default=1)
    issue_id = fields.Many2one('project.issue', string='Issue')

    @api.multi
    def assign_procedure(self):
        self.issue_id.assign_procedure(
            procedure=self.procedure_id, sequence=self.sequence,
        )
        return True
