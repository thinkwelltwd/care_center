# -*- coding: utf-8 -*-
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
    
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Sales',
    'version': '0.4',

    'depends': [
        'care_center',
        'crm_phonecall',
        'sale_crm',
    ],

    'data': [
        'views/crm_lead2task_wizard.xml',
        'views/crm_lead.xml',
        'views/crm_phonecall.xml',
        'views/project_task.xml',
        'views/add_phonecall.xml',
    ],
}
