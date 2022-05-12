from odoo import api, fields, models


class CrmPhonecallToTaskWizard(models.TransientModel):
    """
    Convert a Phone Call into a Project Task.
    """

    _name = "crm.phonecall2task.wizard"
    _description = 'Care Center CRM Phone Call To Task Wizard'
    # crm.partner.binding is removed in Odoo 14
    #_inherit = 'crm.partner.binding'

    def _get_partner_id(self):
        return self.env['crm.phonecall'].browse(
            self.env.context.get('active_id')
        ).partner_id

    def _get_project_id(self):
        return self.env['crm.phonecall'].browse(
            self.env.context.get('active_id')
        ).project_id

    partner_id = fields.Many2one('res.partner', string='Customer', default=_get_partner_id)
    project_id = fields.Many2one('project.project', string='Project', default=_get_project_id)

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

    def action_phonecall_to_task(self):
        """
        Create a Task from Phonecall details
        """
        self.ensure_one()
        Task = self.env['project.task']
        ProjectTags = self.env['project.tags']

        phonecall_id = self.env['crm.phonecall'].browse(
            self.env.context.get('active_id')
        )

        tags = ProjectTags.search([('name', 'in', [tag.name for tag in phonecall_id.tag_ids])])
        partner_id = phonecall_id.partner_id
        company_id = partner_id.company_id.id
        if partner_id:
            email_from = partner_id.email
        else:
            email_from = None

        task_id = Task.with_company(company_id).create({
            'name': phonecall_id.name,
            'project_id': self.project_id.id,
            'partner_id': partner_id.id,
            'description': phonecall_id.description,
            'email_from': email_from,
            'priority': phonecall_id.priority,
            'phone': phonecall_id.partner_phone or False,
            'company_id': company_id,
            'tag_ids': [(6, 0, [tag.id for tag in tags])],
        })
        vals = {
            'task_id': task_id.id,
            'state': 'done',
        }
        phonecall_id.write(vals)

        return {
            'name': 'Task created',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('project.view_task_form2').id,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': task_id.id,
        }
