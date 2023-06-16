{
    'name': "Care Center HR",
    'summary': """Extend HR features for Care Center.""",
    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",
    'category': 'Human Resources',
    'version': '15.0.1.0.0',
    'depends': [
        'care_center',
        'hr_timesheet_attendance',
    ],
    'data': [
        'report/hr_attendance.xml',
        'report/hr_timesheet_attendance.xml',
    ],
}
