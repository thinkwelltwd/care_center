# -*- coding: utf-8 -*-
{
    'name': "care_center_contacts",

    'summary': """
        Extend Contacts features for Care Center.""",

    'description': """
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Tools',
    'version': '0.1',

    'depends': [
        'contacts',
        'crm_phonecall',
        'support_team',
    ],

    'data': [
        'views/contacts.xml',
    ],
}
