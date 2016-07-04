# -*- coding: utf-8 -*-
from openerp import api, tools
from openerp.osv import fields, osv
from datetime import datetime
from openerp import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class wizard_payment_due1(osv.osv_memory):
    _name = 'wizard.payment.due1'
    _inherit = ['mail.thread']
    
    def get_name(self, cr, uid, context=None):
       return str(datetime.strftime(datetime.today(), "%d%m%Y"))

    _columns = {
    			'date_from' : fields.date('Date From'),
    			'date_to' : fields.date('Date To'),
                'invoice_ids':fields.many2many('account.invoice', string='Filter on invoices',help="Only selected invoices will be E-Mail to Customers"),
                'partner_ids':fields.many2many('res.partner', 'partner_payment_due_rel', 'wizard_pd_id', 'partner_id', 'Partners'), 
				'state': fields.selection([('draft','New'), ('sent','Sent')], 'State'),
				'temp_wiz_id': fields.many2one('wizard.payment.due1.temp', 'Temp Wizard'),
				'temp_wiz_id1': fields.many2one('wizard.payment.email.log', 'Temp Wizard'),
				'name': fields.char('Date'),
    }

    _defaults = {
		'state' : 'draft',
		'name': get_name,
	}

    def onchange_date_from(self, cr, uid, ids, date_from, date_to, context=None):
    	res = {'value':{
                      'invoice_ids':[],
					  'temp_wiz_id': False
                      }
            }
        #invoice_ids = self.pool.get('account.invoice').search(cr, uid,[('type','=','out_invoice'),('state','=','open'),('date_invoice','>=',date_from),('date_invoice','<=',date_to)])
        #res['value'].update({
        #            'invoice_ids': [[6,0,invoice_ids]],
        #})
        #if invoice_ids:
        #    cr.execute("""delete from wizard_payment_due1_temp""")
        #    wizard_id = self.pool.get('wizard.payment.due1.temp').create(cr, uid, {})
        #    self.pool.get('account.invoice').write(cr, uid, invoice_ids, {'temp_id': wizard_id}, context)
        #    res['value'].update({'temp_wiz_id': wizard_id})
        return res

    def show_invoice_list(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids):
            invoice_ids = self.pool.get('account.invoice').search(cr, uid,[('type','=','out_invoice'),('state','=','open'),('date_invoice','>=',rec.date_from),('date_invoice','<=',rec.date_to)])
            if invoice_ids:
                cr.execute("""delete from wizard_payment_due1_temp""")
                wizard_id = self.pool.get('wizard.payment.due1.temp').create(cr, uid, {})
                self.pool.get('account.invoice').write(cr, uid, invoice_ids, {'temp_id': wizard_id}, context)
                self.write(cr, uid, ids, {'temp_wiz_id': wizard_id})

            return {
	   			'type': 'ir.actions.act_window',
				'name': 'Invoices',
				'res_model': 'wizard.payment.due1.temp',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': int(rec.temp_wiz_id.id),
				'target': 'new',
				'context': context,
			}

    def show_log_list(self, cr, uid, ids, context=None):
    	print"CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",context

    	# for rec in self.browse(cr, uid,ids):
    	# 	wizard_id = self.pool.get('wizard.payment.email.log').create(cr, uid, {})
    	# 	print"rec.id  ",rec
    	# 	self.pool.get('wizard.payment.email.log.detail').write(cr, 1, ids, {'temp_id': wizard_id},context)
     #    	self.write(cr, uid, ids, {'temp_wiz_id1': wizard_id})
     	# if context is None: context = {}
      #   # no call to super!
      #   res={}
      #   proj_list = []
      #   proj_obj=self.pool.get('wizard.payment.email.log.detail')
      #   proj_list = proj_obj.search(cr, uid, [])  
      #   print proj_list    
      #   context.update({'default_val':True})     
        # if proj_list:
        # 	res.update({'log_list':[(6,0,proj_list)]})

    	return {
   			'type': 'ir.actions.act_window',
			'name': 'Batch Invoice Logs',
			'res_model': 'wizard.payment.email.log',
			'view_type': 'form',
			'view_mode': 'form',
			# 'res_id': int(rec.temp_wiz_id1.id),
			'view_id':'view_wizard_payment_email_log',
			'target': 'new',
			'context': context,
		}


    def send_mail(self, cr, uid, ids, context=None):
		""" Send Report by Email
		"""
		inv_obg = self.pool.get('wizard.payment.email.log.detail')
		for rec in self.browse(cr, uid, ids):
			ctx = {}
			val_email_log = {}
			ir_model_data = self.pool.get('ir.model.data')
			invoices = [invoice.id for invoice in rec.invoice_ids]
			res = {}
			for invoice in rec.invoice_ids:
				res[invoice.partner_id.id] = []
			for invoice in rec.invoice_ids:
				res[invoice.partner_id.id].append(invoice.id)

			for partner in res:
				if len(res[partner]) == 1:
					try:
						template_id = ir_model_data.get_object_reference(cr, 1, 'o2b_batch_email', 'email_template_edi_invoice_dup3')[1]
					except ValueError:
						template_id = False
					try:
						compose_form_id = ir_model_data.get_object_reference(cr, 1, 'mail', 'email_compose_message_wizard_form')[1]
					except ValueError:
						compose_form_id = False 
					ctx = dict(ctx)
					val_email_log = dict(val_email_log)
					print"partner###",res[partner][0]
					print"partner.email_send###",partner
					ctx.update({
						'default_model': 'account.invoice',
						'default_res_id': res[partner][0],
						'default_use_template': bool(template_id),
						'default_template_id': template_id,
						#'default_type': 'comment',
						'default_partner_ids': [[6,0,[partner]]]
						})
					val_email_log.update({
						'invoice_id':res[partner][0],
						'partner_id':partner,
						})
					mail_id = self.pool.get('mail.compose.message').create(cr, 1, {}, context=ctx)
					self.pool.get('mail.compose.message').send_mail(cr, 1, [mail_id])
					self.write(cr, uid, ids, {'state': 'sent'})
					print"I am called for Single",res[partner]
					inv_obg.create_record(cr,1,ids,val_email_log,context=context)
				else:
					print"I am called for Multiple",res[partner]
					partner_inv_id = self.pool.get('partner.invoice.alpha').create(cr, uid, {
										'partner_id':partner,
										'invoice_ids': [[6, 0, res[partner]]]
										})
					try:
						template_id = ir_model_data.get_object_reference(cr, 1, 'o2b_batch_email','email_template_edi_multi_invoice_alpha2')[1]
					except ValueError:
						template_id = False
					try:
						compose_form_id = ir_model_data.get_object_reference(cr, 1, 'mail', 'email_compose_message_wizard_form')[1]
					except ValueError:
						compose_form_id = False 
					ctx = dict(ctx)
					val_email_log = dict(val_email_log)
					print"partner.email_send###",partner
					ctx.update({
						'default_model': 'partner.invoice.alpha',
						'default_res_id': partner_inv_id,
						'default_use_template': bool(template_id),
						'default_template_id': template_id,
						#'default_type': 'comment',
						'default_partner_ids': [[6,0, [partner]]]
						})
					val_email_log.update({
						'partner_id':partner,
						'partner_inv_id':res[partner],
						})
					mail_id = self.pool.get('mail.compose.message').create(cr, 1, {}, context=ctx)
					send = self.pool.get('mail.compose.message').send_mail(cr, 1, [mail_id])
					self.write(cr, uid, ids, {'state': 'sent'})
					print"I am called for Multiple",res[partner]
					inv_obg.create_record(cr,1,ids,val_email_log,context=context)
		return True

class wizard_payment_due1_temp(osv.osv):
    _name = 'wizard.payment.due1.temp'
    
    _columns = {
                'invoice_list': fields.one2many('account.invoice', 'temp_id', string='Filter on invoices', help="Only selected invoices will be E-Mail to Customers"),
    }

    def action_add_selected(self, cr, uid, ids, context=None):
        flag = False
        for rec in self.browse(cr, uid, ids):
            for inv in rec.invoice_list:
                if inv.temp_check: flag = True
            if not flag:
                raise osv.except_osv(('Error!'), ('No Invoice Selected!\nPlease select at least one Invoice.'))
            invoices = []
            invs = [invoices.append(inv.id) for inv in rec.invoice_list if inv.temp_check is True]
            if context:
                model = context.get('active_model', False)
                res_id = context.get('active_id', False)
                if model and res_id:
                    self.pool.get(model).write(cr, uid, [res_id], {'invoice_ids': [[6,0,invoices]]})
            return self.pool.get('account.invoice').write(cr, uid, invoices, {'temp_check': False})

    def action_add_all(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids):
            invoices = []
            invs = [invoices.append(inv.id) for inv in rec.invoice_list]
            if context:
                model = context.get('active_model', False)
                res_id = context.get('active_id', False)
                if model and res_id:
                    self.pool.get(model).write(cr, uid, [res_id], {'invoice_ids': [[6,0,invoices]]})
            return self.pool.get('account.invoice').write(cr, uid, invoices, {'temp_check': False})

    def action_select_all(self, cr, uid, ids, context=None):
        invoices = []
        for rec in self.browse(cr, uid, ids):
            invs = [invoices.append(inv.id) for inv in rec.invoice_list]
            self.pool.get('account.invoice').write(cr, uid, invoices, {'temp_check': True})
            return {
				'type': 'ir.actions.act_window',
				'res_model': self._name,
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_id': int(rec.id),
				'target': 'new'	
			}

    def action_deselect_all(self, cr, uid, ids, context=None):
        invoices = []
        for rec in self.browse(cr, uid, ids):
            invs = [invoices.append(inv.id) for inv in rec.invoice_list]
            self.pool.get('account.invoice').write(cr, uid, invoices, {'temp_check': False})
            return {
				'type': 'ir.actions.act_window',
				'res_model': self._name,
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_id': int(rec.id),
				'target': 'new'	
			}
class account_invoice(osv.osv):
    _inherit = "account.invoice"

    _columns = {
		'temp_id': fields.many2one('wizard.payment.due1.temp', 'Payment Due Temp Id'),
		'temp_check': fields.boolean('Check'),
		'email_send': fields.char(string='Accounting Email',related='partner_id.email_send', store=True, readonly=True),
	}

