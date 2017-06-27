# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectUtils(models.AbstractModel):
    _name = 'project.utils'
    _description = "Utils for Issues and Tasks"

    invoiceable = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('contract', 'Contract'),
        ('confirm', 'Confirm'),
    ],
        string='Invoicable',
        default='yes',
        help='Default invoice status for timesheets. Can be '
             'overridden per each timesheet entry.'
    )

    @api.one
    def _user_clocked_in(self):

        clocked_in_count = self.timesheet_ids.search_count([
            ('full_duration', '=', 0.0),
            ('date_stop', '=', False),
            ('user_id', '=', self.env.uid),
            ('project_id', '=', self.project_id.id),
        ])

        if clocked_in_count > 0:
            self.user_clocked_in = True
        else:
            self.user_clocked_in = False

    user_clocked_in = fields.Boolean(
        string='Clocked In',
        compute='_user_clocked_in',
        help='Current user is working on this Issue',
    )

    @api.multi
    def action_start(self):

        clocked_in_somewhere = self.timesheet_ids.search_count([
            ('full_duration', '=', 0.0),
            ('date_stop', '=', False),
            ('project_id', '!=', False),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_somewhere:
            raise UserError(_(
                'You are already working and can\'t record multiple '
                'timesheets at once. Check the "Work In Progress" filter '
                'and Stop any "Work In Progress" timesheet(s).'
            ))

        Factor = self.env['hr_timesheet_invoice.factor']
        if not self.invoiceable or self.invoiceable == 'yes':
            factor = Factor.search([('name', '=', 'Yes')])
        elif self.invoiceable == 'confirm':
            factor = Factor.search([('name', '=', 'Confirm')])
        else:
            factor = Factor.search([('name', '=', 'No')])
        factor = factor and factor[0].id

        self.write({
            'timesheet_ids': [(0, 0, {
                'name': 'Work In Progress',
                'date_start': datetime.now(),
                'account_id': self.project_id.analytic_account_id.id,
                'company_id': self.env.user.company_id.id,
                'user_id': self.env.uid,
                'project_id': self.project_id.id,
                'to_invoice': factor,
             })]
        })

    @api.multi
    def action_stop(self):
        """
        Wizard to close timesheet, but allow the user to
        edit the work description and closing time.
        """
        if not self.project_id:
            raise UserError(_(
                'Please specify a project before closing Timesheet.'
            ))

        timesheet = self.timesheet_ids.search([
            ('full_duration', '=', 0.0),
            ('date_stop', '=', False),
            ('project_id', '!=', False),
            ('user_id', '=', self.env.uid),
            ('project_id', '=', self.project_id.id),
        ])
        if not timesheet:
            raise UserError(_(
                'No open timesheet for %s' % self.env.user_id.name
            ))
        if len(timesheet) > 1:
            raise UserError(_(
                'Multiple open timesheets found for this Issue/Task. '
                'Stop any running "Work In Progress" timesheet(s) manually.'
            ))

        wizard_form = self.env.ref('care_center_timesheets.timesheet_timer_wizard', False)
        Timer = self.env['timesheet_timer.wizard']
        current_total_time = 0.0
        for ticket in self.timesheet_ids:
            current_total_time += ticket.unit_amount

        new = Timer.create({
            'current_total_time': current_total_time * 60,
            'timesheet_id': timesheet.id,
            'to_invoice': timesheet.to_invoice.id,
        })

        return {
            'name': 'Record Issue Timesheet Log',
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet_timer.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
