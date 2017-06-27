# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CrmPhonecall(models.Model):
    _inherit = "crm.phonecall"

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        string='Issue',
    )
    description = fields.Html('Description')

    @api.onchange('partner_id')
    def _partner_id(self):
        """
        Filter Issues by Partner, including all
        Issues of Partner Parent or Children
        """
        partner = self.partner_id
        issue = self.issue_id
        opportunity = self.opportunity_id

        if not partner:
            return {
                'domain': {
                    'issue_id': [],
                    'opportunity_id': [],
                }
            }

        # Always get ALL issues related to the company,
        # whether the partner_id is Company or Contact
        partner_ids = [partner.id]
        parent_id = partner.parent_id and partner.parent_id.id or partner.id
        partner_ids.extend(
                [rp.id for rp in self.env['res.partner'].search([('parent_id', '=', parent_id)])]
            )

        domain = [
            '|',
            ('partner_id', '=', False),
            ('partner_id', 'in', partner_ids),
        ]
        # Reset fields ONLY if the partner doesn't match! Otherwise, will always
        # clear partner_id field, due onchange methods on issue_id / opportunity_id
        if issue and issue.partner_id and issue.partner_id.id not in partner_ids:
            self.issue_id = False
        if opportunity and opportunity.partner_id and opportunity.partner_id.id not in partner_ids:
            self.opportunity_id = False

        return {
            'domain': {
                'issue_id': domain,
                'opportunity_id': domain,
            },
        }

    @api.onchange('issue_id')
    def _issue_id(self):
        """
        Set Team if possible. Search by name, to handle
        CRM & Support Teams which have different FKs
        """
        if not self.issue_id:
            return
        if self.issue_id.team_id:
            team = self.env['crm.team'].search([('name', '=', self.issue_id.team_id.name)])
            self.team_id = team and team.id

        # Issues with blank partners shouldn't erase self.partner_id!
        if self.issue_id.partner_id and self.issue_id.partner_id != self.partner_id:
            self.partner_id = self.issue_id.partner_id.id

    @api.onchange('opportunity_id')
    def _opportunity_id(self):
        if self.opportunity_id and self.opportunity_id.team_id:
            self.team_id = self.opportunity_id.team_id.id

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
