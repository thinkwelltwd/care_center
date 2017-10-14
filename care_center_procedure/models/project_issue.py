# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    procedure_ids = fields.One2many('procedure.assignment', 'issue_id',
                                    string='Procedures',
                                    domain=[('procedure_id.parent_id', '=', False)],
                                    )

    checklist_ids = fields.One2many('procedure.assignment', 'issue_id',
                                    string='Checklist',
                                    domain=[('procedure_id.parent_id', '!=', False)],
                                    )
    procedure_count = fields.Integer(compute='_procedure_count')
    checklist_count = fields.Integer(compute='_checklist_count')

    @api.multi
    def _procedure_count(self):
        self.procedure_count = len(self.procedure_ids)

    @api.multi
    def _checklist_count(self):
        self.checklist_count = len(self.checklist_ids)

    @api.multi
    def assign_procedure(self, procedure, sequence):
        """Assign a procedure to this issue"""
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
                'procedure_id': proc.id,
                'sequence': sequence,
                'issue_id': self.id,
            })

    def _delete_related_checklists(self, assigned_procedures):
        """
        Delete child procedures when parent procedure assignment is removed
        """
        deletes = []
        for proc_assignment in assigned_procedures:
            if proc_assignment[0] == 2:
                procedure = self.env['procedure.assignment'].browse(proc_assignment[1])
                deletes.append(procedure.procedure_id.id)

        if deletes:
            self.env['procedure.assignment'].search([
                ('issue_id', '=', self.id),
                ('procedure_id.parent_id', 'in', deletes),
            ]).unlink()

    def write(self, vals):
        if 'procedure_ids' in vals:
            self._delete_related_checklists(assigned_procedures=vals['procedure_ids'])
        return super(ProjectIssue, self).write(vals)

    @api.multi
    def confirm_checklists_done(self):
        open_checklists = self.env['procedure.assignment'].search_count([
            ('issue_id', '=', self.id),
            ('status', 'in', ['todo', 'waiting', 'working'])
        ])
        if open_checklists:
            raise ValidationError(
                'Please close all open Checklists'
            )

    @api.multi
    def close_issue(self):
        self.confirm_checklists_done()
        return super(ProjectIssue, self).close_issue()

    @api.multi
    def toggle_active(self):
        if self.active:
            self.confirm_checklists_done()
        return super(ProjectIssue, self).toggle_active()
