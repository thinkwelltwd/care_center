# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
        ('4', 'Crisis'),
        ('5', 'Disaster'),
    ], 'Priority', index=True, default='0')
