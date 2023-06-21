{
    'name': "Care Center Contacts",
    'summary': """Extend Contacts features for Care Center.""",
    'author': "Dave Burkholder <dave@thinkwelldesigns.com>",
    'website': "http://www.thinkwelldesigns.com",
    'category': 'Tools',
    'version': '15.0.1.0.0',
    'depends': [
        'contacts',
        'care_center',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/contacts.xml',
        'views/res_partner.xml',
        'views/extra_contactinfo.xml',
    ],
    'license': 'LGPL-3',
}
