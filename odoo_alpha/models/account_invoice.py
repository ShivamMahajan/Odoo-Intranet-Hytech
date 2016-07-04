# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
#    Coded by: Borni DHIFI  (dhifi.borni@gmail.com)
#
#-------------------------------------------------------------------------------

from openerp import models, fields, api, _

class account_invoice(models.Model):
    _inherit = "account.invoice"
         
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, states={'draft': [('readonly', False)]})
    partner_contact_id  = fields.Many2one('res.partner', string='Site Contact',  readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res=super(account_invoice,self).onchange_partner_id(type, partner_id, date_invoice,payment_term, partner_bank_id, company_id)  
        #get delivry adress
        if partner_id:
            part = self.pool.get('res.partner').browse(self._cr, self._uid, partner_id)
            addr = self.pool.get('res.partner').address_get(self._cr, self._uid, [part.id], ['delivery', 'invoice', 'contact'])
            res['value'].update( {'partner_shipping_id': addr['delivery'] })
            #get domain for delivery , invoicing , contact
            delivery_ids=[]
            contact_ids=[]
            for child in part.child_ids:
                if child.type =='delivery': 
                    delivery_ids.append(child.id)
                if child.type =='contact': 
                    contact_ids.append(child.id)                     
            if not delivery_ids : delivery_ids.append(part.id)  
            if not contact_ids : contact_ids.append(part.id)
            domain_delivery= [('id','in', delivery_ids)]
            domain_contact= [('id','in', contact_ids)]
            res_domain={'domain': {'partner_shipping_id': domain_delivery,  'partner_contact_id':domain_contact}}
            res.update(res_domain)
        return  res
account_invoice()
