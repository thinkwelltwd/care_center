from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from ..utils import get_factored_duration


class MoveTimesheetOrPause(models.TransientModel):
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


class MoveTimesheet(models.TransientModel):
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
        origin_task = self.origin_task_id
        destination_task = self.destination_task_id
        company_id = destination_task.company_id.id
        aa = destination_task.project_id.analytic_account_id

        active_timesheet = self.destination_task_id.has_active_timers(
            singleton=True,
            user_id=self.timesheet_id.user_id,
        )

        if active_timesheet:
            return self._merge_active_timesheets(active_timesheet)

        user = self.env['res.users'].browse([self.env.context.get('user_id', self.env.uid)])
        sheet_id = user.get_hr_timesheet_id(origin_task.company_id.id)
        if destination_task.company_id != origin_task.company_id:
            sheet_id = user.get_hr_timesheet_id(destination_task.company_id.id)

        self.timesheet_id.with_context(force_company=company_id).sudo().write({
            # have to include date in vals, for cost calculation in project_timesheet_currency
            'date': self.timesheet_id.date,
            'task_id': destination_task.id,
            'company_id': company_id,
            'project_id': destination_task.project_id.id,
            'partner_id': destination_task.partner_id.id,
            'account_id': aa and aa.id,
            'so_line': None,  # will be set when destination Task is closed
            'sheet_id': sheet_id,
        })

        if self.timesheet_id.timer_status in ('running', 'paused'):
            destination_task._handle_timesheet_reminder_activity()
        self.origin_task_id.delete_timesheet_reminder_activity()

        return True

    @api.multi
    def _merge_active_timesheets(self, destination_timesheet):
        """
        Merge original timesheet values with destination and then dele
        """
        self.timesheet_id.pause_timer_if_running()

        resume_timer = destination_timesheet.pause_timer_if_running()
        updated_time = destination_timesheet.full_duration + self.timesheet_id.full_duration

        if not resume_timer and self.timesheet_id.timer_status in ('running', 'paused'):
            resume_timer = True

        destination_timesheet.write({
            'full_duration': updated_time,
        })

        self.origin_task_id.delete_timesheet_reminder_activity()
        self.destination_task_id._handle_timesheet_reminder_activity()
        self.timesheet_id.unlink()

        if resume_timer:
            self.destination_task_id.timer_resume()

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


class MoveTimesheetOrSplit(models.TransientModel):
    _name = 'move_timesheet_or_split.wizard'
    _description = 'Move Timesheet or Split'

    origin_task_id = fields.Many2one('project.task', string='Current Task')
    destination_task_id = fields.Many2one('project.task', string='New Task')
    timesheet_id = fields.Many2one('account.analytic.line', string='Current Timesheet')
    ts_action = fields.Selection(
        selection=[
            ('split', 'Move partial time of Current Timesheet to New Task'),
            ('move', 'Move Current Timesheet to New Task'),
        ],
        required=True,
        string='Action',
    )
    time_to_move = fields.Float(string='Time To Move')
    description = fields.Char(string='Time Description')
    needs_description = fields.Boolean(default=False)

    @api.onchange('destination_task_id', 'ts_action')
    def check_needs_description(self):
        if not self.destination_task_id.has_active_timers(
                singleton=True,
                user_id=self.timesheet_id.user_id,
        ) and self.ts_action == 'split':
            self.needs_description = True
        else:
            self.needs_description = False

    @api.constrains('needs_description')
    def _constrain_needs_description(self):
        if self.needs_description and not self.description:
            raise UserError(_('You must give a description for this timesheet.'))

    @api.multi
    def process_time(self):
        self.ensure_one()

        if self.ts_action == 'split':
            SplitTS = self.env['split_timesheet_between_tasks.wizard']
            split_ts = SplitTS.create({
                'origin_task_id': self.origin_task_id.id,
                'destination_task_id': self.destination_task_id.id,
                'timesheet_id': self.timesheet_id.id,
                'time_to_move': self.time_to_move,
                'description': self.description,
            })
            split_ts.process_time()
        else:
            MoveTS = self.env['move_timesheet_to_task.wizard']
            mvts = MoveTS.create({
                'origin_task_id': self.origin_task_id.id,
                'destination_task_id': self.destination_task_id.id,
                'timesheet_id': self.timesheet_id.id,
            })
            mvts.process_time()
        return True


class SplitTimesheet(models.TransientModel):
    _name = 'split_timesheet_between_tasks.wizard'
    _description = 'Split Timesheet between origin & new task'

    def _origin_task(self):
        return self.env.context.get('active_id', None)

    origin_task_id = fields.Many2one('project.task', string='Origin Task', default=_origin_task)
    destination_task_id = fields.Many2one('project.task', string='Destination Task', required=True)
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet', required=True)
    time_to_move = fields.Float(string='Time To Move', required=True)
    description = fields.Char(string='Time Description')

    @api.multi
    def process_time(self):
        self.split_timesheet()

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
    def split_timesheet(self):

        self.ensure_one()

        self.handle_origin_timesheet()
        self.handle_destination_timesheet()

        return True

    @api.multi
    def handle_origin_timesheet(self):

        self.timesheet_id.pause_timer_if_running()

        full_duration = self.timesheet_id.full_duration
        if self.time_to_move > full_duration:
            raise UserError(_(f"Time to move exceeds Timesheet duration of {round(full_duration, 2)}!"))
        elif not (self.time_to_move > 0):
            raise UserError(_("Time to move can not be less than 00:01"))

        updated_time = self.timesheet_id.full_duration - self.time_to_move
        unit_amount = get_factored_duration(
            hours=updated_time,
            invoice_factor=self.timesheet_id.factor,
        )
        self.timesheet_id.write({
            'full_duration': updated_time,
            'unit_amount': unit_amount,
        })

        return True

    @api.multi
    def handle_destination_timesheet(self):

        destination_timesheet = self.destination_task_id.has_active_timers(
            singleton=True,
            user_id=self.timesheet_id.user_id,
        )

        if not destination_timesheet:
            unit_amount = get_factored_duration(
                hours=self.time_to_move,
                invoice_factor=self.timesheet_id.factor,
            )
            return self.destination_task_id._create_timesheet(
                time=self.time_to_move,
                timer_status='stopped',
                name=self.description,
                unit_amount=unit_amount,
                factor=self.timesheet_id.factor,
            )

        resume_timer = destination_timesheet.pause_timer_if_running()

        updated_time = destination_timesheet.full_duration + self.time_to_move
        destination_timesheet.write({
            "full_duration": updated_time,
        })

        if resume_timer:
            self.destination_task_id.timer_resume()

        return True
