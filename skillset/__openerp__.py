# -*- coding: utf-8 -*-
{
    'name': "Skill Set",

    'summary': """
        create and edit the skill sets""",

    'description': """
        Creating the skill sets for the Employees
    """,

    'author': "Deepak Nayak",
    'website': "http://www.hytechpro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views.xml',
    ],
    
}
