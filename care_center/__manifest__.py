# -*- coding: utf-8 -*-
{
    'name': "Care Center",

    'summary': """
        Odoo Help Desk & Ticketing System inspired by osTicket,
        and various other Odoo modules.""",

    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Support',
    'version': '0.1',

    'depends': [
        'utm',
        'crm_phonecall',
        'project',
        'project_issue',
        'support_team',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'data/utm.xml',
        'views/fetchmail_server.xml',
        'views/res_config.xml',
        'views/project_issue.xml',
        'views/care_center.xml',
    ],
    'installable': True,
    'auto_install': False,
}
