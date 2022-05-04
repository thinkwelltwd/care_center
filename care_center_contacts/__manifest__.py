{
    'name': "care_center_contacts",

    'summary': """
        Extend Contacts features for Care Center.""",

    'description': """
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Tools',
    'version': '14.0.1.0.0',

    'depends': [
        'contacts',
        'base_phone',
        'care_center',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/contacts.xml',
        'views/res_partner.xml',
        'views/extra_contactinfo.xml',
    ],
}
