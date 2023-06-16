{
    'name': "Care Center Task Assignment",
    'summary': """
        Assign / Escalate Tasks to new Users or Teams.""",
    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",
    'category': 'Support',
    'version': '15.0.1.0.0',
    'depends': [
        'care_center',
        'web_domain_field',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/task_assignment.xml',
        'views/task_reassignment_wizard.xml',
        'views/project_task.xml',
    ],
    'installable': True,
    'application': True,
}
