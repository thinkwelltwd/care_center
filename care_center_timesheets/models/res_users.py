from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    previous_running_timesheet = fields.Many2one(
        'account.analytic.line',
        string='Previous Running Timesheet',
    )

    @api.multi
    def get_active_timesheet(self):
        """
        Return the active timesheet of this user
        """
        self.ensure_one()
        AccountAnalyticLine = self.env['account.analytic.line'].sudo()
        return AccountAnalyticLine.search(
            [
                ('timer_status', '=', 'running'),
                ('user_id', '=', self.id),
            ],
            limit=1,
        )
