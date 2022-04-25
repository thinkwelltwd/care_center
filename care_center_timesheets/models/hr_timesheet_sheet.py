from odoo import fields, models, api


class Sheet(models.Model):
    _inherit = 'hr_timesheet.sheet'

    def _get_timesheet_sheet_company(self):
        self.ensure_one()
        company = self.env.context.get('company_id', None)
        if company:
            return self.env['res.company'].browse(company)
        return super()._get_timesheet_sheet_company()
