{
    'name': 'Automate Project Creation',
    'version': '1.0',
    'category': 'Project Management',
    'sequence': 14,
    'description': """
This module is used to create project from sale order form.
===========================================================
Features of this module :
1. This application form a bridge between sale and project.

2. It allow sale person to directly interect with development team and accountant.

    """,
    'author': 'Deepak Nayak',
    'website': 'http://hytechpro.org',
    'depends': ['base','sale','project'],
    'data': [
       # 'wizard/create_sale_project_view.xml',
        'security/ir.model.access.csv',
        'project_sale_extends_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}