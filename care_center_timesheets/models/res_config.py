# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TimesheetConfiguration(models.TransientModel):
    _inherit = 'project.config.settings'

    minutes_increment = fields.Float(
        string='Minutes Increment',
        help='Start & Stop time minute rounding increment (rounding up)',
    )
    minimum_work_log = fields.Float(
        string='Mininum Work Duration',
        help='Minumum duration of all timesheets (in minutes)',
    )

    @api.multi
    def set_minutes_increment(self):
        self.env['ir.config_parameter'].set_param(
            'start_stop.minutes_increment', self.minutes_increment,
            groups=['base.group_system'],
        )

    @api.multi
    def set_minimum_work_log(self):
        self.env['ir.config_parameter'].set_param(
            'start_stop.minimum_work_log', self.minimum_work_log,
            groups=['base.group_system'],
        )

    @api.model
    def get_default_values(self, fields):
        Param = self.env['ir.config_parameter']
        increment = Param.get_param('start_stop.minutes_increment', default=0.0)
        min_work = Param.get_param('start_stop.minimum_work_log', default=0.0)
        return {
            'minutes_increment': float(increment),
            'minimum_work_log': float(min_work),
        }

    @api.model
    def default_get(self, fields):
        res = super(TimesheetConfiguration, self).default_get(fields)
        Param = self.env['ir.config_parameter']
        increment = Param.get_param('start_stop.minutes_increment', default=0.0)
        min_work = Param.get_param('start_stop.minimum_work_log', default=0.0)
        res.update({
            'minutes_increment': float(increment),
            'minimum_work_log': float(min_work),
        })
        return res
