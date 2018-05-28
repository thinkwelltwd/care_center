# -*- coding: utf-8 -*-
{
    'name': "Care Center Time Sheets",

    'summary': """
        Extend Timesheets for Care Center.""",

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Projects and Sales',
    'version': '0.3',

    'depends': [
        'hr_timesheet_sheet',
        'project',
        'support_team',
    ],

    'data': [
        'data/invoice_factors.xml',
        'security/ir.model.access.csv',
        'report/project_task_template.xml',
        'report/timesheets_report.xml',
        'report/timesheets_template.xml',
        'views/hr_timesheet.xml',
        'views/project_task.xml',
        'views/res_config.xml',

        # Wizard Views
        'views/timesheet_timer.xml',
        'views/move_timesheet.xml',
    ],
}
