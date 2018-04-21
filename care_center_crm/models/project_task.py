from odoo import models, fields, api


class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['care_center.base', 'project.task']

    phonecall_ids = fields.One2many(
        comodel_name='crm.phonecall',
        inverse_name='task_id',
        string='Phonecalls',
    )
    phonecall_count = fields.Integer(
        compute='_phonecall_count',
        string="Phonecalls",
    )

    @api.multi
    def _phonecall_count(self):
        for task in self:
            task.phonecall_count = self.env['crm.phonecall'].search_count(
                [('task_id', '=', task.id)],
            )
