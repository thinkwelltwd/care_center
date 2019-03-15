from odoo import api, fields, models
from odoo.exceptions import UserError


class CrmLeadToTaskWizard(models.TransientModel):
    """
    Convert a Lead into a Project Task and
    move the Mail Thread and Attachments.
    """

    _name = "crm.lead2task.wizard"
    _inherit = 'crm.partner.binding'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Customer')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('partner_id')
    def set_project_domain(self):
        domain = []
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.partner_id.parent_id:
            domain.append(('partner_id', '=', self.partner_id.parent_id.id))
            domain.insert(0, '|')

        return {
            'domain': {'project_id': domain}
        }

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
        team = self.env['crm.team'].search([
            '|',
            ('name', '=', name),
            ('name', '=', '%s Support' % name),
        ], limit=1)
        return team and team.id

    def move_phonecalls(self, task_id):
        task_calls = self.env['crm.phonecall'].search([(
            'opportunity_id', '=', self.id,
        )])
        task_calls.write({
            'opportunity_id': False,
            'task_id': task_id,
        })

    def move_attachments(self, task_id):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', self.id),
        ])
        attachments.write({
            'res_model': 'project.task',
            'res_id': task_id,
        })

    @api.multi
    def action_lead_to_task(self):
        self.ensure_one()
        lead = self.lead_id
        if not self.partner_id:
            raise UserError('Lead must have a partner assigned to create Task')

        task = self.env['project.task'].create({
            'name': lead.name,
            'description': lead.description,
            'project_id': self.project_id.id,
            'partner_id': lead.partner_id.id,
            'user_id': lead.user_id and lead.user_id.id,
            'medium_id': lead.medium_id and lead.medium_id.id,
            'team_id': self.get_team_id(lead=lead),
            'tag_ids': [(6, 0, self.get_tag_ids(lead=lead))]
        })
        lead.message_change_thread(task)
        self.move_attachments(task_id=task.id)
        self.move_phonecalls(task_id=task.id)

        lead.write({'active': False})

        return {
            'name': 'Task created',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('project.view_task_form2').id,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': task.id,
        }
