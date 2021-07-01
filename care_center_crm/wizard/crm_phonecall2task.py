from odoo import api, fields, models


class CrmPhonecallToTaskWizard(models.TransientModel):
    """
    Convert a Phone Call into a Project Task.
    """

    _name = "crm.phonecall2task.wizard"
    _description = 'Care Center CRM Phone Call To Task Wizard'
    _inherit = 'crm.partner.binding'

    partner_id = fields.Many2one('res.partner', string='Customer')
    phonecall_id = fields.Many2one('crm.phonecall', string='Phone Call')
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
            'domain': {
                'project_id': domain,
            },
        }

    @api.multi
    def action_phonecall_to_task(self):
        """
        Create a Task from Phonecall details
        """
        self.ensure_one()
        Task = self.env['project.task']
        ProjectTags = self.env['project.tags']

        tags = ProjectTags.search([('name', 'in', [tag.name for tag in self.phonecall_id.tag_ids])])
        partner_id = self.phonecall_id.partner_id
        company_id = partner_id.company_id.id
        if partner_id:
            email_from = partner_id.email
        else:
            email_from = None

        task_id = Task.with_context(force_company=company_id).create({
            'name': self.phonecall_id.name,
            'project_id': self.project_id.id,
            'partner_id': partner_id.id,
            'description': self.phonecall_id.description,
            'email_from': email_from,
            'priority': self.phonecall_id.priority,
            'phone': self.phonecall_id.partner_phone or False,
            'company_id': company_id,
            'tag_ids': [(6, 0, [tag.id for tag in tags])],
        })
        vals = {
            'task_id': task_id.id,
            'state': 'done',
        }
        self.phonecall_id.write(vals)

        return {
            'name': 'Task created',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('project.view_task_form2').id,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': task_id.id,
        }
