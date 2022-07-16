import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MergeTasks(models.TransientModel):
    _inherit = 'merge.task.wizard'

    def action_merge(self):
        super(MergeTasks, self).action_merge()
        self.merge_procedures()
        return True

    def merge_procedures(self):
        """Move procedures into destination task"""
        dst_procedures = self.dst_task_id.mapped('procedure_ids.procedure_id.id')
        ProcedureAssignment = self.env['procedure.assignment']

        for task in self.task_ids:
            if task.id == self.dst_task_id.id:
                continue

            for procedure_assignment in task.procedure_ids:
                if procedure_assignment.procedure_id in dst_procedures:
                    continue

                ProcedureAssignment.search([
                    ('task_id', '=', task.id),
                ]).write({
                    'task_id': self.dst_task_id.id,
                })

                dst_procedures.append(procedure_assignment.procedure_id)
