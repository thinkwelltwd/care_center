{
    'name': "care_center_crm",

    'summary': """
        Extend CRM features for Care Center.""",

    'description': """
    Add smart buttons to enable easy conversion to other record types.
        * Convert Tasks to Opportunities.
        * Convert Opportunities to Tasks.
        * Create Tasks from Phonecalls.
        * Link Tasks to existing Phonecalls.
        * Add Timesheets to Phonecalls.
    
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Sales',
    'version': '14.0.1.0.0',
    'conflicts': ['crm_phonecall_timesheet'],
    'depends': [
        'care_center',
        'sale_crm',
    ],

    'data': [
        'views/crm_lead2task_wizard.xml',
        'views/crm_phonecall2task_wizard.xml',
        'views/crm_lead.xml',
        'views/crm_phonecall.xml',
        'views/project_task.xml',
        'views/add_phonecall.xml',
        'views/crm_phonecall_to_phonecall.xml',
        'views/systray.xml',
    ],
}
