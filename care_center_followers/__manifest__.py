{
    'name': "Care Center Followers",
    'summary': """Enable disabling followers on models such as Sale Orders, Invoices.""",
    'description': """
        Enable disabling followers on models such as Sale Orders, Invoices.
    """,
    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",
    'category': 'Tools',
    'version': '15.0.1.0.0',
    'depends': [
        'account',
        'sale',
        'care_center',
        'purchase',
    ],
    'data': [
        'views/res_config.xml',
    ],
}
