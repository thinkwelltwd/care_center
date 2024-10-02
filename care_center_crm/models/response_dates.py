from odoo import models, fields
from datetime import timedelta


class TaskResponseDates(models.AbstractModel):
    _name = 'crm.response_dates'
    _description = 'Dates to provide a response by'

    in_30_days = fields.Datetime(compute='_compute_days')
    in_90_days = fields.Datetime(compute='_compute_days')

    def _compute_days(self):
        self.in_30_days = fields.Datetime.now() + timedelta(30)
        self.in_90_days = fields.Datetime.now() + timedelta(90)
