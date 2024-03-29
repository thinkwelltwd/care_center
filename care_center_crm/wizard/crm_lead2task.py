from lchttp import json_dumps

from odoo import api, fields, models
from odoo.exceptions import UserError


class CrmLeadToTaskWizard(models.TransientModel):
    """
    Convert a Lead into a Project Task and
    move the Mail Thread and Attachments.
    """
    _name = "crm.lead2task.wizard"
    _description = 'Care Center CRM Lead To Task Wizard'

    project_id = fields.Many2one('project.project', string='Project')
    project_id_domain = fields.Char(
        compute='_compute_project_id_domain',
        readonly=True,
        store=False,
    )

    @api.depends('project_id')
    def _compute_project_id_domain(self):
        for rec in self:
            lead = rec.get_lead()
            domain = []
            if lead.partner_id:
                domain.append(('partner_id', '=', lead.partner_id.id))
            if lead.partner_id.parent_id:
                domain.append(('partner_id', '=', lead.partner_id.parent_id.id))
                domain.insert(0, '|')
            rec.project_id_domain = json_dumps(domain)

    def get_tag_ids(self, lead):
        """
        When converting Task to Opportunity, carry Tags over if name is exact match
        """
        if not lead.tag_ids:
            return []
        tag_names = lead.tag_ids.mapped('name')
        return self.env['project.tags'].search([('name', 'in', tag_names)]).mapped('id')

    def get_team_id(self, lead):
        """
        When converting Opportunity to Task, carry Team over,
        if Suffix is Sales instead of Support
        """
        if not lead.team_id:
            return False
        name = lead.team_id.name
        if name.lower().endswith('sales'):
            name = name[:7].strip()
        team = self.env['crm.team'].search(
            [
                '|',
                ('name', '=', name),
                ('name', '=', '%s Support' % name),
            ],
            limit=1,
        )
        return team and team.id

    def move_phonecalls(self, lead_id, task_id):
        task_calls = self.env['crm.phonecall'].search([
            ('opportunity_id', '=', lead_id),
        ])
        task_calls.write({
            'opportunity_id': False,
            'task_id': task_id,
        })

    def move_attachments(self, lead_id, task_id):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', lead_id),
        ])
        attachments.write({
            'res_model': 'project.task',
            'res_id': task_id,
        })

    def action_lead_to_task(self):
        self.ensure_one()
        lead = self.get_lead()
        if not lead.partner_id:
            raise UserError('Lead must have a partner assigned to create Task')

        company_id = lead.partner_id.company_id.id
        Task = self.env['project.task'].with_company(company_id)
        user_id = lead.user_id and lead.user_id.id
        task_id = Task.create({
            'name': lead.name,
            'description': lead.description,
            'project_id': self.project_id.id,
            'partner_id': lead.partner_id.id,
            'user_ids': [(6, 0, [user_id])] if user_id else False,
            'medium_id': (lead.medium_id and lead.medium_id.id) or False,
            'team_id': self.get_team_id(lead=lead),
            'company_id': company_id,
            'tag_ids': [(6, 0, self.get_tag_ids(lead=lead))]
        })
        lead.message_change_thread(task_id)
        self.move_attachments(lead_id=lead.id, task_id=task_id.id)
        self.move_phonecalls(lead_id=lead.id, task_id=task_id.id)

        lead.active = False
        return {
            'name': task_id.name,
            'view_mode': 'form',
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': task_id.id,
            'target': 'current',
        }

    def get_lead(self):
        return self.env['crm.lead'].browse(self.env.context.get('active_id'))
