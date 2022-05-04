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
    'version': '14.0.1.0.0',

    'depends': [
        'base',
        'analytic',
    ],

    'data': [
        'views/analytic_account.xml',
        'views/res_partner.xml',
    ],
}
