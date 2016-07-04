# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------------


{
    'name': 'Customer Invoice Report',
    'version': '1.0',
    'description': '''
       - Customer Invoice Report
    ''',
    'category': 'Generic Modules',
	'website': 'http://o2b.co.in',
    'author': 'O2B Technologies',
    'depends': ['odoo_alpha','account','partner_abn_acn_willow', 'mail'],
    'data':[
			'wizard/print_payment_due1.xml',
			'views/report_invoice.xml',
            'views/report_invoice_custom_batch.xml',
            'res_partner_view.xml',

            'views/report_multi_invoice.xml',
            'data/email_tmplate.xml',
            'security/ir.model.access.csv',
            ],
    'installable': True,
    'active': False,
  }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
