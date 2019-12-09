{
    'name': "care_center_contacts",

    'summary': """
        Extend Contacts features for Care Center.""",

    'description': """
    """,

    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",

    'category': 'Tools',
    'version': '12.0.1.0.0',

    'depends': [
        'note',
        'contacts',
        'crm_phonecall',
        'support_team',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/contacts.xml',
        'views/res_partner.xml',
        'views/extra_contactinfo.xml',
    ],
}
