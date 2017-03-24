# -*- coding: utf-8 -*-
{
    'name': "service_partner",

    'summary': """
        Add service_partner field to analytic_account
        for use in Care Center functionality.""",

    'description': """
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Support',
    'version': '0.1',

    'depends': [
        'base',
        'analytic',
    ],

    'data': [
        'views/analytic_account.xml',
        'views/res_partner.xml',
    ],
}
