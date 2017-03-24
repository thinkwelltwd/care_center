# -*- coding: utf-8 -*-
# © 2017 Dave Burkholder <dave@thinkwelldesigns.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Support Teams',
    'version': '1.0',
    'category': 'Support',
    'summary': 'Manage Support Teams on Issues & Tasks',
    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",

    'depends': [
        'base',
        'mail',
        'project',
        'project_issue',
    ],
    'data': [
        'security/support_team.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/support_team.xml',
        'views/project_task.xml',
        'views/project_issue.xml',
     ],
    'installable': True,
    'auto_install': False,
}
