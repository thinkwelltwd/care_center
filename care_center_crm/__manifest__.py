# -*- coding: utf-8 -*-
{
    'name': "care_center_crm",

    'summary': """
        Extend CRM features for Care Center.""",

    'description': """
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Sales',
    'version': '0.3',

    'depends': [
        'care_center',
        'crm_phonecall',
    ],

    'data': [
        'views/crm_phonecall.xml',
        'views/project_task.xml',
        'views/add_phonecall.xml',
    ],
}
