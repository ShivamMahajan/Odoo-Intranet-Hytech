# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
#    Coded by: Borni DHIFI  (dhifi.borni@gmail.com)
#
#-------------------------------------------------------------------------------

from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
         'partner_contact_id': fields.many2one('res.partner', 'Site Contact', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Contact partner for current sales order."),
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res=super(sale_order,self).onchange_partner_id(cr, uid, ids, part, context=context)
        if not part:
            return res
        #get domain for delivery , invoicing , contact
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        delivery_ids=[]
        invoice_ids=[]
        contact_ids=[]
        for child in part.child_ids:
            if child.type =='delivery': 
                delivery_ids.append(child.id)
            if child.type =='invoice': 
                invoice_ids.append(child.id)
            if child.type =='contact': 
                contact_ids.append(child.id) 
                
        if not delivery_ids : delivery_ids.append(part.id)  
        if not invoice_ids : invoice_ids.append(part.id)  
        if not contact_ids : contact_ids.append(part.id)  
        
        domain_delivery= [('id','in', delivery_ids)]
        domain_invoice= [('id','in',invoice_ids)]
        domain_contact= [('id','in', contact_ids)]
        
        res_domain={'domain': {'partner_invoice_id': domain_invoice, 'partner_shipping_id': domain_delivery,  'partner_contact_id':domain_contact}}
        res.update(res_domain)
        return  res
        
          
    def _prepare_invoice(self, cr, uid, order, lines, context=None): 
        '''
        Create invoice from  sale order .
        Add partner_contact_id and partner_shipping_id in invoice_vals
        '''
        res=super(sale_order,self)._prepare_invoice(cr, uid, order, lines, context=context)
        res.update({'partner_shipping_id':order.partner_shipping_id and order.partner_shipping_id.id or False ,
                    'partner_contact_id':order.partner_contact_id and order.partner_contact_id.id or False ,
                      })
        return res
        


    def copy(self, cr, uid, id, default=None, context=None):
        default = dict(context or {})
        sale = self.browse(cr, uid, id, context=context)
        default.update(
            origin=sale.name or '',
            date_order=sale.date_order,
            client_order_ref=sale.client_order_ref )
        return super(sale_order, self).copy(cr, uid, id, default, context=context)
           
    
sale_order()
