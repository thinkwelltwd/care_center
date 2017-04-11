# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CrmPhonecall(models.Model):
    _inherit = "crm.phonecall"

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        string='Issue',
    )
    description = fields.Html('Description')

    @api.multi
    def convert_issue(self):
        """
        Convert a phone call to an issue
        """
        Issue = self.env['project.issue']
        ProjectTags = self.env['project.tags']
        issue = {}
        for call in self:
            tags = ProjectTags.search([('name', 'in', [tag.name for tag in call.tag_ids])])
            partner_id = call.partner_id
            if partner_id:
                email_from = partner_id.email
            else:
                email_from = None

            issue_id = Issue.create({
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
                'issue_id': issue_id.id,
                'state': 'done',
            }
            call.write(vals)
            issue[call.id] = issue_id
        return issue

    @api.multi
    def action_button_make_issue(self):
        """
        Convert a phonecall into an issue and then redirect to the issue view.
        """
        issue = {}
        for call in self:
            issue = call.convert_issue()
            return issue[call.id].redirect_issue_view()
        return issue
