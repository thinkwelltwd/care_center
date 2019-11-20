from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MoveTimeheetOrPause(models.TransientModel):
    _name = 'move_timesheet_or_pause.wizard'
    _description = 'Move Timesheet or Pause'

    origin_task_id = fields.Many2one('project.task', string='Current Task')
    destination_task_id = fields.Many2one('project.task', string='New Task')
    timesheet_id = fields.Many2one('account.analytic.line', string='Current Timesheet')
    ts_action = fields.Selection(
        selection=[
            ('pause', 'Pause Current Timesheet'),
            ('move', 'Move Current Timesheet to New Task'),
        ],
        required=True,
        string='Action',
    )

    @api.multi
    def process_time(self):
        self.ensure_one()

        if self.ts_action == 'pause':
            self.origin_task_id.timer_pause()
            self.destination_task_id._create_timesheet()
        else:
            MoveTS = self.env['move_timesheet_to_task.wizard']
            mvts = MoveTS.create({
                'origin_task_id': self.origin_task_id.id,
                'destination_task_id': self.destination_task_id.id,
                'timesheet_id': self.timesheet_id.id,
            })
            mvts.process_time()
        return True


class MoveTimeheet(models.TransientModel):
    _name = 'move_timesheet_to_task.wizard'
    _description = 'Move Timesheet to a new task'

    def _origin_task(self):
        return self.env.context.get('active_id', None)

    origin_task_id = fields.Many2one('project.task', string='Origin Task', default=_origin_task)
    destination_task_id = fields.Many2one('project.task', string='Destination Task')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet')

    @api.constrains('destination_task_id')
    def check_project(self):
        if not self.destination_task_id.project_id:
            raise ValidationError(
                '%s does not have a project assigned' % self.destination_task_id.name
            )

    @api.multi
    def process_time(self):
        self.ensure_one()
        if self.timesheet_id.timer_status == 'running':
            self.move_time_only()
        else:
            self.move_timesheet()

        task_form = self.env.ref('project.view_task_form2', False)
        return {
            'name': 'Destination Task',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': self.destination_task_id.id,
            'view_id': task_form.id,
            'view_type': 'form',
            'view_mode': 'form',
        }

    @api.multi
    def move_timesheet(self):
        """
        Move the entire timesheet to the new task
        """
        self.ensure_one()
        task = self.destination_task_id
        aa = task.project_id.analytic_account_id

        self.timesheet_id.write({
            # have to include date in vals, for cost calculation in project_timesheet_currency
            'date': self.timesheet_id.date,
            'task_id': task.id,
            'project_id': task.project_id.id,
            'partner_id': task.partner_id.id,
            'account_id': aa and aa.id,
            'so_line': task.sale_line_id and task.sale_line_id.id,
        })

        return True

    def reset_original_timesheet_start(self):
        """
        Chop off the time of the current session, and
        reset date_start on original timesheet
        """
        end = datetime.now()
        start = fields.Datetime.to_datetime(self.timesheet_id.date_start)
        session_duration = (end - start).total_seconds()

        self.timesheet_id.write({
            'date_start': start - timedelta(seconds=session_duration),
            'timer_status': 'paused',
        })

    @api.multi
    def move_time_only(self):
        """
        If the timesheet was paused multiple times, and has more than
        just the current session, create a timesheet with that amount
        of time and and reset the original sheet start time & run status.
        """
        self.ensure_one()
        has_previous_session = self.timesheet_id.full_duration

        # if the current timesheet was never paused, just move the whole thing
        if not has_previous_session:
            return self.move_timesheet()

        task = self.destination_task_id
        timesheet = self.timesheet_id
        aa = task.project_id.analytic_account_id

        # yapf: disable
        self.env['account.analytic.line'].create({
            'name':  'Work In Progress',
            'task_id': task.id,
            'project_id': task.project_id.id,
            'partner_id': task.partner_id.id,
            'account_id': aa and aa.id,
            'timer_status': 'running',
            'date': timesheet.date,
            'date_start': timesheet.date_start,
            'factor': timesheet.factor and timesheet.factor.id,
            'sheet_id': timesheet.sheet_id and timesheet.sheet_id.id,
            'user_id': timesheet.user_id.id,
            'company_id': task.company_id.id,
            'so_line': task.sale_line_id and task.sale_line_id.id,
        })
        # yapf: enable

        self.reset_original_timesheet_start()
