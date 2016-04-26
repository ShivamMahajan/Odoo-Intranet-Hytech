
{
    'name': 'HR Announcement',
    'version': '1.0',
    'author': 'Deepak Nayak',
    'category': 'Human Resources',
    'sequence': 21,
    'summary': 'Company Internal Announcement',
    'description': """
        Company Internal Announcement
    """,
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'hr_announcement_view.xml',
        'hr_announcement_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    
}