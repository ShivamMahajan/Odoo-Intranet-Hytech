{
    'name': 'Leaves Extends For Intranet',
    'version': '1.0',
    'category': 'Leave Management',
    'sequence': 14,
    'description': """
This module is used to maintain leaves of every employees. 
==================================
Features of this module :
Only Reporting amnager is able to approve the leaves.
Things to be take care:
1. Every leave type must have double validation rule.
2. HR manager have right to approve every leave.

    """,
    'author': 'Deepak Nayak',
    'website': 'http://hytechpro.org',
    'depends': ['base','hr','hr_holidays'],
    'data': [
       # 'wizard/create_sale_project_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/leave_reason_view.xml',
        'hr_leave_extends_view.xml',
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}