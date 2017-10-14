# -*- coding: utf-8 -*-
{
    'name': "Care Center Procedures",

    'summary': """
        Add Procedures to Tasks and Issues. 
        """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    "category": "Project Management",
    'version': '0.1',

    'depends': [
        'project_issue',
        'care_center',
        'support_team',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/assign_procedure_wizard.xml',
        'views/project_issue.xml',
        'views/procedure.xml',
    ],
}
