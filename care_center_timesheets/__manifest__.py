# -*- coding: utf-8 -*-
{
    'name': "Care Center Time Sheets",

    'summary': """
        Extend Timesheets for Care Center.""",

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Projects and Sales',
    'version': '0.2',

    'depends': [
        'hr_timesheet',
        'project_issue_sheet',
        'support_team',
    ],

    'data': [
        'data/invoice_factors.xml',
        'security/ir.model.access.csv',
        'report/project_issue_template.xml',
        'report/project_task_template.xml',
        'report/timesheets_report.xml',
        'report/timesheets_template.xml',
        'views/hr_timesheet.xml',
        'views/project_issue.xml',
        'views/project_task.xml',
        'views/res_config.xml',
        'views/timesheet_timer.xml',
    ],
}
