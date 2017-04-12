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
        'crm_phonecall',
        'project',
        'project_issue',
        'support_team',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config.xml',
        'views/care_center.xml',
    ],
    'installable': True,
    'auto_install': False,
}
