# -*- coding: utf-8 -*-
{
    'name': "Care Center",

    'summary': """
        Odoo Help Desk & Ticketing System inspired by osTicket,
        and various other Odoo modules.""",

    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Support',
    'version': '12.0.1.0.0',

    'depends': [
        'base_automation',
        'utm',
        'note',
        'calendar',
        'crm_phonecall',
        'support_team',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'data/utm.xml',
        'views/fetchmail_server.xml',
        # 'views/project.xml',
        'views/res_config.xml',
        'views/res_partner.xml',
        'views/project_task.xml',
        'views/base_automation.xml',
        'views/care_center.xml',

        # Wizard Views
        'views/merge_tasks_wizard.xml',
        'views/update_project_info.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
