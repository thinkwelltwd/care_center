{
    'name': "Care Center Internal CRM",
    'summary': """Streamline internal company communications between employees.""",
    'description': """Handle timesheets and phone logs for inter-company communication on Tasks.""",
    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",
    'category': 'Sales',
    'version': '15.0.1.0.0',
    'depends': [
        'care_center_timesheets',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/utm_sources.xml',
        'views/project_task.xml',
        'views/add_internal_phonecall.xml',
        'views/end_internal_phonecall.xml',
    ],
}
