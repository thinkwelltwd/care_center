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
        'hr_timesheet_sheet',
        'care_center',
        'web',
    ],

    'data': [
        'data/mail_activity_type.xml',
        'data/invoice_factors.xml',
        'security/ir.model.access.csv',
        'report/project_task_template.xml',
        'report/timesheets_report.xml',
        'report/timesheets_template.xml',
        'views/hr_timesheet.xml',
        'views/project_task.xml',
        'views/res_config.xml',
        'views/sale.xml',
        'views/systray.xml',

        # Wizard Views
        'views/timesheet_timer.xml',
        'views/move_timesheet.xml',
    ],

    'qweb': [
        'static/src/xml/systray.xml',
    ],
}
