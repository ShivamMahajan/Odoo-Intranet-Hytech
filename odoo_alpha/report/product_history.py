# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.report import report_sxw


class product_history(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(product_history, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_products':self._get_products,
            'get_plus':self._get_plus,
            'get_minus':self._get_minus,
        })
    def _get_products(self,products_ids):
        product_obj=self.pool.get("product.product")
        if not products_ids :
            products_ids=product_obj.search(self.cr,self.uid,[])
        product_obj_list=product_obj.browse(self.cr,self.uid,products_ids)
        return product_obj_list
    
    def _get_plus(self,date_from,date_to,product):
        s_plus=0
        domain=[('type','=','in_invoice'),('state','!=','draft'),('state','!=','cancel')]
        if date_from and date_to :
            domain.append(('date_invoice','>=',date_from))
            domain.append(('date_invoice','<=',date_to))
        account_invoice_in=self.pool.get("account.invoice").search(self.cr,self.uid,domain)
        account_line_receipt=self.pool.get("account.invoice.line").search(self.cr,self.uid,[('product_id','=',product.id),('invoice_id','in',account_invoice_in)])
        for line in self.pool.get("account.invoice.line").browse(self.cr,self.uid,account_line_receipt):
            s_plus+=line.quantity
        return s_plus
     
    def _get_minus(self,date_from,date_to,product):
        s_minus=0
        domain=[('type','=','out_invoice'),('state','!=','draft'),('state','!=','cancel')]
        if date_from and date_to :
            domain.append(('date_invoice','>=',date_from))
            domain.append(('date_invoice','<=',date_to))
        account_invoice_out=self.pool.get("account.invoice").search(self.cr,self.uid,domain)
        account_line_receipt=self.pool.get("account.invoice.line").search(self.cr,self.uid,[('product_id','=',product.id),('invoice_id','in',account_invoice_out)])
        for line in self.pool.get("account.invoice.line").browse(self.cr,self.uid,account_line_receipt):
            s_minus+=line.quantity
        return s_minus
    
    

class report_product_history(osv.AbstractModel):
    _name = 'report.odoo_alpha.report_product_history'
    _inherit = 'report.abstract_report'
    _template = 'odoo_alpha.report_product_history'
    _wrapped_report_class = product_history

