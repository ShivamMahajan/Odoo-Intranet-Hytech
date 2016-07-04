# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date,datetime

class Overdue(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Overdue, self).__init__(cr, uid, name, context=context)
 
        self.localcontext.update({
            #'docs': docs,
            'time': time,
            'get_partners':self._get_partners,
            'getLines': self._lines_get,
            'total_balance': self._total_balance,
            'get_month_balance':self._get_month_balance
        })
        self.context = context
    
    def _get_partners(self,partner):
        partner_obj = self.pool['res.partner']
        if partner:
            docs = partner_obj.browse(self.cr, self.uid, partner)
        else:
            ids=partner_obj.search(self.cr,self.uid,[])
            docs = partner_obj.browse(self.cr, self.uid, ids)
        return docs
    
    def _total_balance(self, partner,date_to):
        movelines=self._lines_get(partner,date_to)
        total=0
        for line in movelines:
            total+=line.debit-line.credit
        return total

    def _lines_get(self, partner,date_to):
        moveline_obj = self.pool['account.move.line']
        cr=self.cr
        if date_to:
            query=""" select account_move_line.id from account_move_line   
                       left join  account_account account  on  account_move_line.account_id = account.id  
                       where account.type = 'receivable'   
                        and  account_move_line.partner_id =%s  
                        and  account_move_line.state != 'draft'  
                        and  account_move_line.date <= '%s'  
                        and  ( account_move_line.reconcile_id IS NULL or 
                             (account_move_line.reconcile_id IS NOT NULL and
                              account_move_line.last_rec_date >  '%s' ) ) 
                          order by account_move_line.date ,account_move_line.move_id """ % (partner.id,str(date_to),str(date_to))
            self.cr.execute(query)
            move_lines_ids=[]
            for  data in self.cr.dictfetchall()  : 
                move_lines_ids.append(data['id'])
        movelines = moveline_obj.browse(self.cr, self.uid, move_lines_ids)
        return movelines

     
    def _get_month_balance(self, partner,date_to):
        movelines=self._lines_get(partner,date_to)
        total_current=0.0
        total_30=0.0
        total_60=0.0
        total_other=0.0
        for line in movelines:
            a=str(line.date).split('-')
            a=int(a[1])
            today=str(date_to).split('-')
            today=int(today[1])
            today_30=today-1
            today_60=today-2
            if a==today:
                total_current+=(line.debit-line.credit)
            elif a==today_30:
                total_30+=(line.debit-line.credit)
            elif a==today_60:
                total_60+=(line.debit-line.credit)     
            else :
                total_other+=(line.debit-line.credit)  
        
        return total_current,total_30,total_60,total_other

 



class report_overdue(osv.AbstractModel):
    _name = 'report.odoo_alpha.report_payment_due_view'
    _inherit = 'report.abstract_report'
    _template = 'odoo_alpha.report_payment_due_view'
    _wrapped_report_class = Overdue

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
