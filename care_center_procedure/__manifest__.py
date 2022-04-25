{
    'name': "Care Center Procedures",

    'summary': """
        Add Procedures to Tasks / Tickets. 
        """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    "category": "Project Management",
    'version': '13.0.1.0.0',

    'depends': [
        'care_center',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/assign_procedure_wizard.xml',
        'views/project_task.xml',
        'views/procedure.xml',
    ],
}
