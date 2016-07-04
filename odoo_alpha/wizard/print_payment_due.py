# -*- coding: utf-8 -*-
from openerp import api, tools
from openerp.osv import fields, osv



class wizard_product_history(osv.osv_memory):
    _name = 'wizard.payment.due'
    
    _columns = {
                'date': fields.date('Date',required=True), 
                'partner_ids':fields.many2many('res.partner', 'partner_payment_due_rel', 'wizard_pd_id', 'partner_id', 'Partners',domain=[('is_company','=',True)]), 
    }

 
        
    def print_report(self, cr, uid, ids, context=None):
       
        if context is None:
            context = {}
        datas = {}
        data = self.browse(cr, uid, ids[0])
        partner_ids= [partner.id for partner in data.partner_ids]
        res={'date': data.date,'partner_ids':  partner_ids}
        datas['form'] = res
        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'odoo_alpha.report_payment_due_view',
            'datas' : datas,
       }