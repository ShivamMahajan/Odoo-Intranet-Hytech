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

from openerp.osv import fields, osv
from openerp import tools

class account_due_statment(osv.osv):
    _name = "account_due.statment"
    _rec_name = 'partner_id'
    _auto = False
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'date_move':fields.date('Date move', readonly=True),
        'date_maturity':fields.date('Date due', readonly=True), 
        'invoice_number':fields.char('Invoice Number', readonly=True),
        'ref':fields.char('Ref', readonly=True),
        'debit':fields.float('Debit', readonly=True),
        'credit':fields.float('Credit', readonly=True),
        'balance':fields.float('Balance', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'period_id': fields.many2one('account.period', 'Period', readonly=True),
    }
    _order = 'date_move,invoice_number'

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
                context=None, count=False):
        for arg in args:
            if arg[0] == 'period_id' and arg[2] == 'current_year':
                current_year = self.pool.get('account.fiscalyear').find(cr, uid)
                ids = self.pool.get('account.fiscalyear').read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
                args.append(['period_id','in',ids])
                args.remove(arg)
        return super(account_due_statment, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order,
            context=context, count=count)

    def read_group(self, cr, uid, domain, *args, **kwargs):
        for arg in domain:
            if arg[0] == 'period_id' and arg[2] == 'current_year':
                current_year = self.pool.get('account.fiscalyear').find(cr, uid)
                ids = self.pool.get('account.fiscalyear').read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
                domain.append(['period_id','in',ids])
                domain.remove(arg)
        return super(account_due_statment, self).read_group(cr, uid, domain, *args, **kwargs)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_due_statment')
        cr.execute("""
            create or replace view account_due_statment as (
                SELECT
                    l.id as id,
                    l.partner_id AS partner_id,
                    am.name AS invoice_number,
                    l.ref AS ref,
                    min(l.date) AS date_move,
                    max(l.date_maturity) AS date_maturity,
                    sum(l.debit) AS debit,
                    sum(l.credit) AS credit,
                    sum(l.debit - l.credit) AS balance,
                    l.company_id AS company_id,
                    l.period_id AS period_id
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                    LEFT JOIN account_move am ON (l.move_id = am.id)
                WHERE
                    a.active AND
                    a.type = 'receivable' AND
                    l.reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                GROUP BY
                    l.id, l.partner_id,am.name,l.ref, l.company_id,  l.period_id
            )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
