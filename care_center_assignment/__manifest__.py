{
    'name': "Care Center Task Assignment",

    'summary': """
        Assign / Escalate Tasks to new Users or Teams.""",

    'author': "Thinkwell Designs",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Support',
    'version': '11.0.1.0.0',

    'depends': [
        'support_team',
        'care_center',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/task_assignment.xml',
        'views/task_reassignment_wizard.xml',
        'views/project_task.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
