# © 2017 Dave Burkholder <dave@thinkwelldesigns.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Support Teams',
    'version': '11.0.1.0.0',
    'category': 'Support',
    'summary': 'Manage Support Teams on Tickets & Tasks',
    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",

    'depends': [
        'crm',
        'sales_team',
        'project',
    ],
    'data': [
        'security/support_team.xml',
        'views/crm.xml',
        'views/project_project.xml',
        'views/support_team.xml',
        'views/project_task.xml',
        'views/support_team_dashboard.xml',
     ],
    'qweb': [
        'static/src/xml/support_team_dashboard.xml',
    ],
    'installable': True,
    'auto_install': False,
}
