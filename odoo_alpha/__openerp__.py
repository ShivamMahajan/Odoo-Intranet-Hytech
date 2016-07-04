# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
#    Coded by: Borni DHIFI  (dhifi.borni@gmail.com)
#
#-------------------------------------------------------------------------------


{
    'name': 'Specific features for Alpha Supply',
    'version': '1.0',
    'description': '''
       - Contacts managment
    ''',
    'category': 'Generic Modules',
    'author': 'Borni DHIFI',
    'depends': ['base','sale','account','stock_account','account_financial_report_webkit'],
    'data':[
            'data/custom_paperformat.xml',
            'view/invoice_view.xml',
            'view/sale_order_view.xml',
            'view/stock_view.xml',
            'report/account_followup_stat_view.xml',
            'wizard/wizard_product_history.xml',
            'wizard/print_payment_due_view.xml',
            'views/product_history_report.xml',
            'views/due_payment_report.xml',
            
            ],
    'installable': True,
    'active': False,
  }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
