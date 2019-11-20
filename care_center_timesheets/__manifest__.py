{
    'name': "Care Center Time Sheets",

    'summary': """
        Extend Timesheets for Care Center.""",

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Projects and Sales',
    'version': '12.0.1.0.0',

    'depends': [
        'sale_timesheet_line_exclude',
        'project',
        'support_team',
        'web',
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
        'views/sale.xml',

        # Wizard Views
        'views/timesheet_timer.xml',
        'views/move_timesheet.xml',
    ],
}
