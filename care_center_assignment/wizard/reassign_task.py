from lchttp import json_dumps

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReassignTaskWizard(models.TransientModel):
    _name = 'reassign_task.wizard'
    _description = 'Reassign Task to User or Team'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
    )
    name = fields.Char(
        string='Summary',
        required=True,
        help='Short explanation for reassigning the Task.',
    )
    description = fields.Html(
        'Description',
        required=False,
        help='Extended explanation for reassigning the Task.',
    )
    reassign_to = fields.Selection(
        selection=[
            ('user', 'User'),
            ('team', 'Team'),
            ('myself', 'Myself'),
        ],
        string='Reassign To',
        required=True,
        default='user',
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        index=True,
        ondelete='set null',
    )
    send_notifications = fields.Boolean(
        'Notify Users',
        default=False,
        help='Send notification emails to all team members.',
    )
    team_id = fields.Many2one(
        'crm.team',
        string='Team',
        index=True,
        ondelete='set null',
        domain=[('type_team', '!=', 'sale')],
        help='New Team responsible for performing this Task',
    )
    reassign_subtasks = fields.Boolean(
        'Reassign Subtasks',
        default=True,
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        required=False,
        domain=[('model_id.model', '=', 'project.task')],
        help="When template is specified, an email will be sent "
             "to all followers of the task being re-assigned.",
    )
    assigned_to_domain = fields.Char(
        compute='_compute_assigned_to_domain',
        readonly=True,
        store=False,
    )

    @api.constrains('assigned_to', 'team_id')
    def verify_assignment_changed(self):
        if self.assigned_to:
            if self.assigned_to in self.task_id.user_ids:
                raise ValidationError(f'The Task is already assigned to {self.assigned_to.name}')

        if self.team_id:
            if self.team_id == self.task_id.team_id:
                raise ValidationError(
                    f'The Task is already assigned to the {self.team_id.name} Team'
                )

    @api.onchange('assigned_to', 'team_id')
    def prefill_description(self):
        if not self.name and not self.task_id.assignment_count:
            self.name = 'Initial Assignment'

    @api.depends('team_id')
    def _compute_assigned_to_domain(self):
        for rec in self:
            rec.assigned_to_domain = json_dumps(
                rec.team_id and [('id', 'in', rec.team_id.member_ids.mapped('id'))] or []
            )

    @api.onchange('reassign_to')
    def reset_assignment(self):
        self.team_id = None
        self_assigned = 'Self-assign Task'

        if self.reassign_to == 'myself':
            self.assigned_to = self.env.uid
            if not self.name:
                self.name = self_assigned
        else:
            self.assigned_to = None
            if self.name == self_assigned:
                self.name = None

    def assignment(self):
        if self.team_id:
            return f'the {self.team_id.name} Team'
        return 'you'

    def get_partner_ids(self):
        if self.assigned_to:
            return [self.assigned_to.partner_id.id]

        member_ids = self.team_id.member_ids.mapped('partner_id.id')
        if self.team_id.user_id:
            member_ids.append(self.team_id.user_id.partner_id.id)
        return member_ids

    def get_subject(self):
        if self.assigned_to:
            return f'{self.env.user.name} has assigned a Task to you'
        return f'{self.env.user.name} has assigned a Task to the {self.team_id.name} Team'

    def get_body(self):
        return """
        <p>{by} has assigned the <b>{task}</b> Task to {assignment} </p>
        <p><b>Summary: </b>{summary}</p>
        <p><b>Description: </b></p>
        {description}
        """.format(
            by=self.env.user.name,
            assignment=self.assignment(),
            summary=self.name,
            task=self.task_id.name,
            description=self.description,
        )

    def notify_partner_email(self):
        """
        When a ticket is assigned to a user, it may be useful to notify
        all followers of the ticket via an email message. More specific
        than Auto Responders.
        """
        if not self.email_template_id:
            return

        self.email_template_id.send_mail(self.task_id.id)

    def reassign_user_team(self):

        team_id = self.team_id and self.team_id.id
        assigned_to = self.assigned_to and self.assigned_to.id
        assignment = self.env['task.assignment'].create({
            'name': self.name,
            'description': self.description,
            'assigned_by': self.env.uid,
            'assigned_to': assigned_to,
            'team_id': team_id,
            'task_id': self.task_id.id,
        })

        if assigned_to:
            user_ids = [(6, 0, [assigned_to])]
        else:
            user_ids = [(5, 0, 0)]

        stats = {
            'user_ids': user_ids,
        }
        if self.team_id:
            stats['team_id'] = self.team_id.id

        if self.reassign_subtasks:
            for subtask in self.task_id._get_all_subtasks():
                subtask.with_context({'tracking_disable': True}).write(stats)

        stats['assignment_ids'] = [(4, assignment.id, None)]
        self.task_id.with_context({'tracking_disable': True}).write(stats)

        if self.send_notifications:
            self.task_id.message_post(
                body=self.get_body(),
                subject=self.get_subject(),
                message_type='email',
                parent_id=False,
                attachments=None,
                content_subtype='html',
                partner_ids=self.get_partner_ids(),
            )

        self.notify_partner_email()
        if self.assigned_to:
            self.task_id.message_subscribe([self.assigned_to.partner_id.id])

        return True
