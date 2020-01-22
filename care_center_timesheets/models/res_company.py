from odoo import api, fields, models
from odoo.tools import date_utils


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def get_current_timesheet_sheet(self):
        """Return Companies current timesheet sheet"""
        self.ensure_one()

        return self.env['hr_timesheet.sheet'].search([
            ('company_id', '=', self.id),
            ('date_start', '=', date_utils.start_of(fields.Date.context_today(self), 'week'))
        ])
