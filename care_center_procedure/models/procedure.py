# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProcedureProcedure(models.Model):
    _name = 'procedure.procedure'
    _order = 'sequence asc'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    description = fields.Html(string='Description')
    parent_id = fields.Many2one('procedure.procedure', string='Procedure', ondelete='cascade',
                                domain=[('parent_id', '=', False)],)
    child_ids = fields.One2many('procedure.procedure', 'parent_id', string='Checklist')
    sequence = fields.Integer('Sequence', default=1)
    tag_ids = fields.Many2many('project.tags', string='Tags')
    documentation = fields.Html('Documentation', compute='_compile_documentation',
                                help='Documentation for this Checklist, or the combined '
                                     'documentation for all the Checklists of this Procedure.',
                                )

    @api.model
    def create(self, vals):
        if 'parent_id' in vals and vals.get('sequence', 1) == 1:
            child_count = self.env['procedure.procedure'].search_count([
                ('parent_id', '=', vals['parent_id'])
            ])
            vals['sequence'] = child_count + 1
        return super(ProcedureProcedure, self).create(vals)

    @api.constrains('parent_id')
    def _limit_depth(self):
        if self.parent_id and self.parent_id.parent_id:
            raise ValidationError(
                '%s is a checklist item and cannot be a parent procedure' % self.parent_id.name
            )

    @api.multi
    def _compile_documentation(self):
        """Combine all checklists descriptions for a given Procedure"""
        for procedure in self:
            if procedure.parent_id:
                continue

            docs = ['<h3>Procedure: %s</h3> %s' % (procedure.name, procedure.description)]
            checklists = self.env['procedure.procedure'].search([
                ('parent_id', '=', procedure.id)
            ])
            for checklist in checklists:
                docs.append('<h3>%s</h3> %s' % (checklist.name, checklist.description))

            procedure.documentation = ''.join(docs)

    @api.multi
    def show_documentation(self):
        """
        Display modal form containing all documentation content
        from this procedure and all child procedures
        """
        form = self.env.ref('care_center_procedure.view_procedure_documentation_form')

        return {
            'name': '%s Documentation' % self.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'procedure.procedure',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.id,
            'views': [
                (form.id, 'form'),
            ],
        }

    @api.multi
    def add_checklist(self):
        """Display modal form to add new checklists"""

        form = self.env.ref('care_center_procedure.view_procedure_checklist_form')

        return {
            'name': 'Add Checklist',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'procedure.procedure',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'parent_id': self.id, 'default_parent_id': self.id, 'hide_checklist': True},
            'views': [
                (form.id, 'form'),
            ],
        }


class ProcedureAssignment(models.Model):
    _name = "procedure.assignment"
    _rec_name = 'procedure_id'
    _order = 'procedure_id asc, sequence asc'

    status = fields.Selection([
        ('done', 'Done'),
        ('todo', 'To Do'),
        ('waiting', 'Waiting'),
        ('working', 'In Progress'),
        ('cancelled', 'Cancelled'),
    ],
     'Status', required=True, copy=False, default='todo')

    procedure_id = fields.Many2one('procedure.procedure', required=True)
    sequence = fields.Integer()
    task_id = fields.Many2one('project.task', 'Ticket',
                              ondelete='cascade', required=False, index=True)
    description = fields.Html('Description', related='procedure_id.description')
    documentation = fields.Html('Documentation', related='procedure_id.documentation')
    recolor = fields.Boolean(compute='_compute_recolor')

    _sql_constraints = [
        ('procedure_task_uniq', 'unique(procedure_id, task_id)', 'A procedure may only be assigned once!'),
    ]

    @api.multi
    def _compute_recolor(self):
        for record in self:
            if record.status == 'todo':
                record.recolor = True

    @api.multi
    def show_documentation(self):
        """
        Display modal form containing all documentation content
        from this procedure and all child procedures
        """
        form = self.env.ref('care_center_procedure.view_procedure_documentation_form')

        return {
            'name': '%s Documentation' % self.procedure_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'procedure.assignment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.id,
            'views': [
                (form.id, 'form'),
            ],
        }

    @api.multi
    def set_parent_procedure_status(self):

        if not self.procedure_id.parent_id:
            return

        procedure = self.procedure_id.parent_id
        unfinished_checklist = self.env['procedure.assignment'].search_count([
            ('procedure_id.parent_id', '=', procedure.id),
            ('task_id', '=', self.task_id.id),
            ('status', 'in', ['todo', 'waiting'])
        ])

        procedure_assignment = self.env['procedure.assignment'].search([
            ('task_id', '=', self.task_id.id),
            ('procedure_id', '=', procedure.id),
        ])

        if unfinished_checklist:
            if procedure_assignment.status != 'working':
                procedure_assignment.write({'status': 'working'})
        else:
            procedure_assignment.write({'status': 'done'})

    @api.multi
    def change_status_done(self):
        for record in self:
            record.status = 'done'
            self.set_parent_procedure_status()

    @api.multi
    def change_status_todo(self):
        for record in self:
            record.status = 'todo'
            self.set_parent_procedure_status()

    @api.multi
    def change_status_cancelled(self):
        for record in self:
            record.status = 'cancelled'
            self.set_parent_procedure_status()

    @api.multi
    def change_status_waiting(self):
        for record in self:
            record.status = 'waiting'
            self.set_parent_procedure_status()
