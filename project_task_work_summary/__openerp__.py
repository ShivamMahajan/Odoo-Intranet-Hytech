# -*- coding: utf-8 -*-
{
    'name': "project_task_work_summary",

    'summary': """
        This module is designed in order to list out all the work summary of the tasks""",

    'description': """
       List all the work summary of the task
    """,

    'author': "Shivam Mahajan",
    'website': "http://www.hytechpro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','project','report_xls'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'task_work_summary_views.xml',
        'report/project_report_view.xml',
        'wizard/project_task_report_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    
}