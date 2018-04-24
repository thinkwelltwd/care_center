# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    procedure_ids = fields.One2many('procedure.assignment', 'task_id',
                                    string='Procedures',
                                    domain=[('procedure_id.parent_id', '=', False)],
                                    )

    checklist_ids = fields.One2many('procedure.assignment', 'task_id',
                                    string='Checklist',
                                    domain=[('procedure_id.parent_id', '!=', False)],
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
        task_planned_hours = self.planned_hours or 0.0

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

            if not proc.parent_id:
                task_planned_hours += proc.planned_hours or 0.0

        self.write({'planned_hours': task_planned_hours})

    def _delete_related_checklists(self, assigned_procedures):
        """
        Delete child procedures when parent procedure assignment is removed
        """
        task_planned_hours = self.planned_hours or 0.0
        deletes = []
        for proc_assignment in assigned_procedures:
            if proc_assignment[0] == 2:
                procedure = self.env['procedure.assignment'].browse(proc_assignment[1])
                deletes.append(procedure.procedure_id.id)

                # subtract planned hours assigned by the parent procedure
                if not procedure.procedure_id.parent_id:
                    task_planned_hours -= procedure.procedure_id.planned_hours

        if task_planned_hours < 0.0:
            task_planned_hours = 0.0
        self.write({'planned_hours': task_planned_hours})

        if deletes:
            self.env['procedure.assignment'].search([
                ('task_id', '=', self.id),
                ('procedure_id.parent_id', 'in', deletes),
            ]).unlink()

    def write(self, vals):
        if 'procedure_ids' in vals:
            self._delete_related_checklists(assigned_procedures=vals['procedure_ids'])
        return super(ProjectTask, self).write(vals)

    @api.multi
    def confirm_checklists_done(self):
        open_checklists = self.env['procedure.assignment'].search_count([
            ('task_id', '=', self.id),
            ('status', 'in', ['todo', 'waiting', 'working'])
        ])
        if open_checklists:
            raise ValidationError(
                'Please close all open Checklists'
            )

    @api.multi
    def close_ticket(self):
        self.confirm_checklists_done()
        return super(ProjectTask, self).close_ticket()

    @api.multi
    def toggle_active(self):
        if self.active:
            self.confirm_checklists_done()
        return super(ProjectTask, self).toggle_active()
