{
    'name': "Care Center Portal",
    'summary': """Allows Portal Users to Create Tickets""",
    'author': "Denver Risser",
    'category': 'Portal',
    'version': '15.0.1.0.0',
    'depends': [
        'base',
        'project',
        'portal',
    ],
    'data': [
        'security/project_security.xml',
        'views/project_portal_templates.xml',
        'views/portal_templates.xml',
    ],
    'license': 'LGPL-3',
}
