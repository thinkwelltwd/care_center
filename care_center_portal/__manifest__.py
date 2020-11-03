# -*- coding: utf-8 -*-
{
    'name': "Care Center Portal",

    'summary': """
        Allows Portal Users to Create Tickets
        """,

    'author': "Denver Risser",
    'category': 'Portal',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'project',
        'portal',
        # 'website_forum',
    ],

    # always loaded
    'data': [
        'security/project_security.xml',
        'views/project_portal_templates.xml',
        'views/portal_templates.xml',
        # 'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/portal_chatter.xml'
    ]
}