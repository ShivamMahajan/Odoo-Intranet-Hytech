# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#
#    Coded by: Borni DHIFI  (dhifi.borni@gmail.com)
#
#-------------------------------------------------------------------------------

from openerp.osv import fields, osv
from openerp.tools.translate import _


class res_partner(osv.osv):
    _inherit = "res.partner"
  

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            res.append((record.id, record.name))
        return res
          
res_partner()
