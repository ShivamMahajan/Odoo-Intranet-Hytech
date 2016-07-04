#-*- coding:utf-8 -*-

from openerp.osv import osv, fields
from datetime import datetime

class partner_invoice_alpha(osv.osv):
	_name = "partner.invoice.alpha"
	_inherit = ['mail.thread']
	_description = "Partner Invoices"
	
	def get_name(self, cr, uid, context=None):
		return str(datetime.strftime(datetime.today(), "%d%m%Y"))

	_columns = {
		'partner_id': fields.many2one('res.partner', 'Partner'),
		'invoice_ids': fields.many2many('account.invoice', 'partner_invoice_alpha_rel', 'partner_alpha_id', 'invoice_id', 'Invoices'),
		'company_id': fields.many2one('res.company', 'Company'),
		'name': fields.char('Name'),
	}

	_defaults = {
		'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
		'name': get_name,
	}

	def print_report(self, cr, uid, ids, context=None):
		return self.pool['report'].get_action(cr, uid, ids, 'o2b_batch_email.report_partner_multi_invoice', context=context)
