{
    'name': "Care Center Portal",
    'summary': """Allows Portal Users to Create Tickets""",
    'author': "Denver Risser",
    'category': 'Portal',
    'version': '14.0.1.0.0',
    'depends': [
        'base',
        'project',
        'portal',
        # 'website_forum',
    ],
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
