# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
#    Coded by: Borni DHIFI  (dhifi.borni@gmail.com)
#
#-------------------------------------------------------------------------------

from openerp.osv import fields, osv

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
         'partner_contact_id': fields.related('sale_id','partner_contact_id', type='many2one', relation='res.partner', string='Site Contact'), 
    }

    '''
    Create invoice from stock.picking .
    Add partner_contact_id and partner_shipping_id in invoice_vals
    '''    
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        res=super(stock_picking,self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=None)
        partner, currency_id, company_id, user_id = key
        if move.picking_id.sale_id:
            res.update({'partner_contact_id' :move.picking_id.sale_id.partner_contact_id and move.picking_id.sale_id.partner_contact_id.id or False})
        if move.picking_id.partner_id:
            res.update({'partner_shipping_id' : move.picking_id.partner_id.id })
        elif move.picking_id.sale_id:
            res.update({'partner_shipping_id' :move.picking_id.sale_id.partner_shipping_id and move.picking_id.sale_id.partner_shipping_id.id or partner.id })
        else:
            res.update({'partner_shipping_id' : partner.id })
        return res
            
stock_picking()            
            
        
        