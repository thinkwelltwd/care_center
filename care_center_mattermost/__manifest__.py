# -*- coding: utf-8 -*-
{
    'name': "Care Center Mattermost",

    'summary': """
        Enable basic Mattermost message notifications from email templates, when the email 
        server setting is a Mattermost server.
        """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Projects and Sales',
    'version': '0.1',

    'depends': [
        'base',
        'mail',
    ],

    'data': [
        'views/ir_mail_server.xml',
        'views/res_partner.xml',
    ],
}
