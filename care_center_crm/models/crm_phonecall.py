from odoo import api, fields, models


class CrmPhonecall(models.Model):
    _name = 'crm.phonecall'
    _description = 'Care Center CRM Phone Call'
    _inherit = ['care_center.base', 'crm.phonecall']

    def _available_task_lead_ids(self):
        """
        Enable dynamic domain filters when Editing
        records where the on_change doesn't fire
        """
        domain = [
            '|',
            ('partner_id', '=', False),
            ('partner_id', 'in', self.get_partner_ids()),
        ]
        self.available_task_ids = self.env['project.task'].search(domain)
        self.available_lead_ids = self.env['crm.lead'].search(domain)

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )

    # Compute these properties so they can serve as domains in xml views
    # active even on Edit mode when partner_id field hasn't been changed
    available_task_ids = fields.Many2many('project.task', compute='_available_task_lead_ids')
    available_lead_ids = fields.Many2many('crm.lead', compute='_available_task_lead_ids')

    description = fields.Html('Description')

    @api.onchange('partner_id')
    def _update_partner_id_domain(self):
        """
        Filter Tasks by Partner, including all
        Tasks of Partner Parent or Children
        """
        partner = self.partner_id
        task = self.task_id
        opportunity = self.opportunity_id

        if not partner:
            return {
                'domain': {
                    'task_id': [],
                    'opportunity_id': [],
                }
            }

        partner_ids = self.get_partner_ids()
        domain = self.get_partner_domain(partner_ids)

        # Reset fields ONLY if the partner doesn't match! Otherwise, will always
        # clear partner_id field, due onchange methods on task_id / opportunity_id
        if task and task.partner_id and task.partner_id.id not in partner_ids:
            self.task_id = False
        if opportunity and opportunity.partner_id and opportunity.partner_id.id not in partner_ids:
            self.opportunity_id = False

        return {
            'domain': {
                'task_id': domain,
                'opportunity_id': domain,
            },
        }

    @api.onchange('task_id')
    def _set_details_from_task(self):
        """
        Set Team if possible. Search by name, to handle
        CRM & Support Teams which have different FKs
        """
        if not self.task_id:
            return
        if self.task_id.team_id:
            team = self.env['crm.team'].search([('name', '=', self.task_id.team_id.name)])
            self.team_id = team and team.id

        # Tasks with blank partners shouldn't erase self.partner_id!
        if self.task_id.partner_id and self.task_id.partner_id != self.partner_id:
            self.partner_id = self.task_id.partner_id.id

        if self.task_id.project_id:
            self.project_id = self.task_id.project_id.id

        if not self.tag_ids and self.task_id.tag_ids:
            tag_names = self.task_id.tag_ids.mapped('name')
            self.tag_ids = self.env['crm.lead.tag'].search([('name', 'in', tag_names)])

    @api.onchange('opportunity_id')
    def _set_opportunity_team(self):
        if self.opportunity_id and self.opportunity_id.team_id:
            self.team_id = self.opportunity_id.team_id.id

    @api.multi
    def create_task(self):
        """
        Create a Task from Phonecall details
        """
        Task = self.env['project.task']
        ProjectTags = self.env['project.tags']
        task = {}
        for call in self:
            tags = ProjectTags.search([('name', 'in', [tag.name for tag in call.tag_ids])])
            partner_id = call.partner_id
            if partner_id:
                email_from = partner_id.email
            else:
                email_from = None

            task_id = Task.create({
                'name': call.name,
                'partner_id': partner_id.id or False,
                'description': call.description or False,
                'email_from': email_from,
                'priority': call.priority,
                'phone': call.partner_phone or False,
                'tag_ids': [(6, 0, [tag.id for tag in tags])],
            })
            vals = {
                'partner_id': partner_id.id,
                'task_id': task_id.id,
                'state': 'done',
            }
            call.write(vals)
            task[call.id] = task_id
        return task

    @api.multi
    def action_button_create_task(self):
        """
        Convert a phonecall into an task and then redirect to the task view.
        """
        task = {}
        for call in self:
            task = call.create_task()
            return task[call.id].redirect_task_view()
        return task
