# -*- coding: utf-8 -*-
from openerp import api, tools
from openerp.osv import fields, osv

class wizard_product_history(osv.osv_memory):
    _name = 'wizard.product.history'
    
    _columns = {
                'date_from': fields.date('Date From'), 
                'date_to': fields.date('To'),
                'product_ids':fields.many2many('product.product', 'move_product_rel', 'wizard_id', 'product_id', 'Products'), 
    }

 
        
    def print_report(self, cr, uid, ids, context=None):
       
        if context is None:
            context = {}
        datas = {}
        data = self.browse(cr, uid, ids[0])
        res={'date_from': data.date_from,'date_to': data.date_to,'product_ids': [p.id for p in data.product_ids]}
        datas['form'] = res
        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'odoo_alpha.report_product_history',
            'datas' : datas,
       }