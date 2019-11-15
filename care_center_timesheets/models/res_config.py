from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    starting_time_offset = fields.Float(
        string='Starting Offset in Minutes',
        help='Offset Timesheet starting time by specified number of minutes',
        config_parameter='start_stop.starting_time_offset',
    )

    minutes_increment = fields.Float(
        string='Minutes Increment',
        help='Start & Stop time minute rounding increment (rounding up)',
        config_parameter='start_stop.minutes_increment',
    )
    minimum_work_log = fields.Float(
        string='Minimum Work Duration',
        help='Minimum duration of all timesheets (in minutes)',
        config_parameter='start_stop.minimum_work_log',
    )
    default_timesheet_invoice_description = fields.Selection(
        selection='_get_timesheet_invoice_description',
        string="Timesheet Invoice Description",
        default_model='sale.order',
        config_parameter='care_center.timesheet_invoice_description',
    )

    @api.model
    def _get_timesheet_invoice_description(self):
        return self.env['sale.order']._get_timesheet_invoice_description()
