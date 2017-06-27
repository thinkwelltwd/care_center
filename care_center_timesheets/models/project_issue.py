# -*- coding: utf-8 -*-
from odoo import models


class ProjectIssue(models.Model):
    _name = 'project.issue'
    _inherit = ['project.utils', 'project.issue']
