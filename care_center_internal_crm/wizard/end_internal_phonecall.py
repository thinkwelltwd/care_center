from odoo import fields, models


class EndInternalPhonecall(models.TransientModel):
    _name = 'end_internal_phonecall.wizard'
    _description = 'End internal phone call'

    name = fields.Char('Call Summary', required=True)
    phonecall_id = fields.Many2one(
        'crm.phonecall',
        name='Phonecall',
        default=lambda self: self.env.context.get('phonecall_id'),
    )

    def end_internal_phonecall(self):
        """
        End phone call, close callee's timesheets and resume callee's previous timesheet
        """
        self.phonecall_id.sudo().with_context(
            timesheet_from_call_duration=False,
        ).write({
            'state': 'done',
            'name': self.name,
        })

        callee = self.phonecall_id.partner_id.get_odoo_user()
        if not callee:
            return

        task_id = self.phonecall_id.task_id
        callee_previous_timesheet = callee.previous_running_timesheet

        # stop the callee's timesheet on this task, if it wasn't stopped manually
        stopped_running_ts = task_id.sudo().with_context(
            calculate_minimum_duration=False,
            user_id=callee.id,
        ).api_timer_stop(summary=self.name)

        if stopped_running_ts and callee_previous_timesheet:
            callee_previous_timesheet.task_id.sudo().with_context(user_id=callee.id).timer_resume()
