# -*- coding: utf-8 -*-
{
    'name': "Care Center Time Sheets",

    'summary': """
        Extend Timesheets for Care Center.""",

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Employees',
    'version': '0.1',

    'depends': [
        'project_issue_code',
        'project_task_code',
    ],

    'data': [
        'report/project_issue_template.xml',
        'report/project_task_template.xml',
        'report/timesheets_report.xml',
        'report/timesheets_template.xml',
    ],
}
