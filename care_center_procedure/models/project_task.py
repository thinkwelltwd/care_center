from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    procedure_ids = fields.One2many(
        'procedure.assignment',
        'task_id',
        string='Procedures',
        domain=[
            ('procedure_id.parent_id', '=', False),
        ],
    )

    checklist_ids = fields.One2many(
        'procedure.assignment',
        'task_id',
        string='Checklist',
        domain=[
            ('procedure_id.parent_id', '!=', False),
        ],
    )
    procedure_count = fields.Integer(compute='_procedure_count')
    checklist_count = fields.Integer(compute='_checklist_count')

    @api.multi
    def _procedure_count(self):
        for task in self:
            task.procedure_count = len(task.procedure_ids)

    @api.multi
    def _checklist_count(self):
        for task in self:
            task.checklist_count = len(task.checklist_ids)

    @api.multi
    def assign_procedure(self, procedure, sequence):
        """Assign a procedure to this Task / Ticket"""
        if sequence == 1:
            sequence = len(self.procedure_ids) + 1

        procedures = self.env['procedure.procedure'].search([
            '|',
            ('id', '=', procedure.id),
            ('parent_id', '=', procedure.id),
        ])

        for proc in procedures:
            # Parent procedure sequence gets defined in wizard
            # checklist procedure sequence carries over
            if proc == procedure:
                sequence = sequence
            else:
                sequence = proc.sequence

            self.env['procedure.assignment'].create({
                'parent_id': proc.parent_id and proc.parent_id.id,
                'procedure_id': proc.id,
                'sequence': sequence,
                'task_id': self.id,
            })

    @api.multi
    def confirm_checklists_done(self):
        open_checklists = self.env['procedure.assignment'].search_count([
            ('task_id', '=', self.id),
            ('status', 'in', ['todo', 'waiting', 'working']),
        ])
        if open_checklists:
            raise ValidationError('Please close all open Checklists')

    @api.multi
    def close_ticket(self):
        self.confirm_checklists_done()
        return super(ProjectTask, self).close_ticket()

    @api.multi
    def toggle_active(self):
        if self.active:
            self.confirm_checklists_done()
        return super(ProjectTask, self).toggle_active()
