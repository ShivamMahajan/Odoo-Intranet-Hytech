from openerp import api, tools
from openerp.osv import fields, osv
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class wizard_payment_email_log(osv.osv_memory):
    _name = 'wizard.payment.email.log'

    _columns = {
    			'log_list':fields.one2many('wizard.payment.email.log.detail', 'temp_id', string='Email Log',help="Email logs"),
                'project_idss':fields.many2many('wizard.payment.email.log.detail','wiz_work_summ_project_rel','work_summ_wiz_id','project_id','Project'),
                'project_domain_idss':fields.many2many('izard.payment.email.log.detail','wiz_work_summ_project_domain_rel','work_id1','mrp_workcenters_domain1','Project Domain'),
         
    }

    def default_get(self, cr, uid, fields, context=None):
         
        if context is None: context = {}
        # no call to super!
        res={}
        # proj_list = []
        # print"YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",context,fields
        # default_val = context.get('default_val',False)
        # print"AAAAAAA",default_val
        # if default_val==True:
        #     print"BBBBBBBBBBBBBBBBBBB"

        proj_obj=self.pool.get('wizard.payment.email.log.detail')
        proj_list = proj_obj.search(cr, uid, []) 
        # proj_list = []
        # proj_obj=self.pool.get('project.project')
        # if uid==1:
        #     proj_list = proj_obj.search(cr, uid, [])           
        # else:
        #     if self.pool['res.users'].has_group(cr, uid, 'project.group_project_sqa'):
        #         proj_list = proj_obj.search(cr, uid, [])
        #     else:    
        #         proj_list = proj_obj.search(cr, uid, [('user_id','=',uid)])    
            
        print"PPPPPPPPPPPPPPPPPPPPPP",proj_list    
        if proj_list:
            print"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        #    if 'log_list' in fields:
            res.update({'project_idss':[(6,0,proj_list)]})
       
        return res

class wizard_payment_email_log_detail(osv.osv_memory):
    _name = 'wizard.payment.email.log.detail'

    _columns = {
            'partner_id' : fields.char('Partner'),
            'date_invoice' : fields.date('Invoice Date'),
            'number':fields.char('Invoice Number'),
            'email_send':fields.char('Accounting Email'),
            'user_id':fields.char('Responsible'),
            'date_due':fields.date('Due Date'),
            'currency_id':fields.char('Currency'),
            'amount_total':fields.char('Total'),
            'temp_id': fields.many2one('wizard.payment.email.log', 'Email Temp Id'),
    }

    def create_record(self, cr, uid,ids,vals, context=None):
        print"Yes I am getting Executed"
        invoice_id = vals.get('invoice_id')
        partner_inv_id = vals.get('partner_inv_id')
        vals_obj = {}
        if invoice_id:
            print"Printing Invoice ID",invoice_id
            vals_obj = dict(vals_obj)
            for rec in self.pool.get('account.invoice').browse(cr, uid,invoice_id,context=context):
                print"rec rec rec",rec.email_send
                vals_obj.update({
                    'partner_id':vals.get('partner_id'),
                    'date_invoice':rec.date_invoice,
                    'number':rec.number,
                    'email_send':rec.email_send,
                    'user_id':rec.user_id,
                    'date_due':rec.date_due,
                    'currency_id':rec.currency_id,
                    'amount_total':rec.amount_total,
                })
                self.create(cr, uid, vals_obj, context=vals_obj)
        if partner_inv_id:
            print"Printing Partner Invoice ID",partner_inv_id
            vals_obj = dict(vals_obj)
            for inv_id in partner_inv_id:
                for rec in self.pool.get('account.invoice').browse(cr, uid,inv_id,context=context):
                    vals_obj.update({
                        'partner_id':vals.get('partner_id'),
                        'date_invoice':rec.date_invoice,
                        'number':rec.number,
                        'email_send':rec.email_send,
                        'user_id':rec.user_id,
                        'date_due':rec.date_due,
                        'currency_id':rec.currency_id,
                        'amount_total':rec.amount_total,
                    })
                    self.create(cr, uid, vals_obj, context=vals_obj)
