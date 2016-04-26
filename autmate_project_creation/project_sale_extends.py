from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, timedelta, date

class project_documents(osv.osv):
	_name  = 'project.documents'
	_description = "Project Related Documents"
	_columns = {
		'name':fields.char('Title',required=True),
		'attached_document':fields.binary("Related Documents",required=True,help="Attached projects related document here"),
		'project_id':fields.many2one('project.project', 'Project Reference', required=True, ondelete='cascade', select=True, readonly=True),
	}

class project_change_requests(osv.osv):
	_name = 'project.change.request'
	_description = "Project Change Request"
	_columns = {
		'name':fields.char('Title',required=True,help="Enter name of Change Request"),
		'description':fields.char('Description',help="Enter the description here"),
		'create_date':fields.datetime("Creation date",readonly=True,help="Creation date for this Change request"),
		'start_date':fields.date('Start Date',help="Working start date for this change request"),
		'end_date': fields.date('End Date',help="Working end date for this change request"),
		'total_revenue':fields.float("Cost",help="Total cost for this Change Request"),
		'project_id':fields.many2one('project.project', 'Project Reference', required=True, ondelete='cascade', select=True, readonly=True),
		'related_sale_order':fields.many2one('sale.order','Sale Order Reference',required=True,ondelete='cascade',readonly=True),
        'customer_id': fields.many2one('res.partner', 'Customer', readonly=True, required=True),
        'user_ids':fields.many2one("res.users","Project Manager",readonly=True,required=True),
	}
	_defaults = {
        'create_date': fields.datetime.now,
	}

	def create(self, cr, uid, vals, context=None):
		sale_order_obj = self.pool.get('sale.order')
		hr_employee_obj = self.pool.get ("hr.employee")
		project_obj = self.pool.get ("project.project")
		today = date.today()
		project_browse_details = project_obj.browse(cr,uid, vals['project_id'])
		vals.update({'user_ids':project_browse_details.user_id.id})
		cr_id = super(project_change_requests, self).create(cr, uid, vals, context=context)
		hr_employee_search = hr_employee_obj.search(cr, uid, [('user_id', '=',project_browse_details.create_uid.id)])
		hr_employee_browse = hr_employee_obj.browse(cr, uid, hr_employee_search)
		sub = "Change request created for project %s" %(project_browse_details.name)
		body_html = '''<html>
							<head></head>
								<body>
									<p> Hi, %s</p>
									<p> In Intranet change request is created for your project. <b> Information of Change Request are :-</b> </p>
									<p> <b> CR Name :- %s </b> </p>
									<p> <b> CR Description :- %s </b> </p>
									<p> <b> Project Name :- %s</b> </p>
									<p> <b> Date Created :- %s </b> </p>
								</body>
					</html>	''' %(project_browse_details.user_id.name, vals['name'], vals['description'], project_browse_details.name, str(today))
		mail_vals = {'state': 'outgoing',
					'subject': sub,
					'body_html': '<pre>%s</pre>' % body_html,
					'email_to': project_browse_details.user_id.login,
					'email_from': hr_employee_browse.work_email ,
					'email_cc':'hytechproerp@gmail.com',
				}
		self.pool.get('mail.mail').create(cr, uid,  mail_vals, context=context)
		return cr_id

class project_new_extends(osv.osv):
	_inherit ='project.project'

	_columns = {
		'pcr_id': fields.one2many('project.change.request', 'project_id', 'Change Request Lines', copy=True),
		'pd_id':fields.one2many('project.documents','project_id','Project Related Documents',copy=True),
		'exist_project':fields.many2one('project.project',"Existing Project",help="Select Existing project"),
		'analytic_account_id': fields.many2one(
            'account.analytic.account', 'Contract/Analytic',
            help="Link this project to an analytic account if you need financial management on projects. "
                 "It enables you to connect projects with budgets, planning, cost and revenue analysis, timesheets on projects, etc.",
            ondelete="cascade", required=True, auto_join=True),
		'use_existing': fields.boolean('Use Existing', help="Check this field when use existing project to create"),
	}

	_defaults = {
		'use_existing':False,
		'use_tasks':True,
		'use_issue':True,
	}

	def create(self, cr, uid, vals, context=None):
		sale_order_obj = self.pool.get('sale.order')
		if context is None:
			context = {}
		create_context = dict(context, project_creation_in_progress=True,
                              alias_model_name=vals.get('alias_model', 'project.task'),
                              alias_parent_model_name=self._name)
		project_id_created = super(project_new_extends, self).create(cr, uid, vals, context=create_context)
		project_details = self.browse(cr, uid, [project_id_created])
		hr_employee_obj = self.pool.get ("hr.employee")
		hr_employee_search = hr_employee_obj.search(cr, uid, [('user_id', '=', project_details.create_uid.id)])
		hr_employee_browse = hr_employee_obj.browse(cr, uid, hr_employee_search)
		sub = "Project Created In Intranet"
		body_html = '''<html>
							<head></head>
								<body>
									<p> Hi, %s</p>
									<p> In Intranet one Project is assigned to you. <b> Information of Project are :-</b> </p>
									<p> <b> Project Name :- %s</b> </p>
									<p> <b> Date Created :- %s </b> </p>
								</body>
						</html>	''' %(project_details.user_id.name, project_details.name, project_details.date_start)
		mail_vals = {'state': 'outgoing',
				'subject': sub,
				'body_html': '<pre>%s</pre>' % body_html,
				'email_to': project_details.user_id.login,
				'email_from': hr_employee_browse.work_email or 'hytechproerp@gmail.com',
				}
		self.pool.get('mail.mail').create(cr, uid,  mail_vals, context=context)
		return project_id_created


	def onchange_exist_project(self,cr,uid,ids,exist_project,context=None):
		res={}
		if exist_project:
			project_name =self.browse(cr,uid,exist_project,context=context)
			res['name']=project_name[0].name
			res['partner_id']=project_name[0].partner_id
		return {'value':res}


class add_sale_cr(osv.osv_memory):
    _name = "add.sale.cr"
    _description = "Adding CR for Existing Projects"

    _columns = {
    	'project_exist':fields.many2one('project.project',"Existing Project",help="Select Existing project"),
    }

    def open_project(self, cr, uid, ids, context=None):
    	""" open a view on one of the given invoice_ids """
    	ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'project', 'edit_project')
        form_id = form_res and form_res[1] or False
        return {
            'name': _('Add Change Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.project',
            'res_id': context.get('project_exist'),
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context':context,
        }



class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _change_request_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0), ids))
        # The current user may not have access rights for sale orders
        try:
            for partner in self.browse(cr, uid, ids, context):
                res[partner.id] = len(partner.change_request_ids)
        except:
            pass
        return res

    _columns = {
        'change_request_count': fields.function(_change_request_count, string='# of Change Request', type='integer'),
        'change_request_ids': fields.one2many('project.change.request','customer_id','Change Request')
    }

    def land_to_quotation_form(self, cr, uid, ids, context=None):
    	mod_obj = self.pool.get('ir.model.data')
    	sale_order_obj = self.pool.get('sale.order')
    	res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
        res_id = res and res[1] or False
        ##########Create Quotation for CR ########
        if 'change_request_type' and 'id' in context:	
        	sale_order_value = {
        			'partner_id':context.get('id'),
        			'change_request_type':context.get('change_request_type'),
       	 	}
       	 	#############Check Quotation is aleady Present or Not
       	 	sale_order_search = sale_order_obj.search(cr, uid, [('partner_id','=',context.get('id')),('change_request_type','=','CR'),('order_line','=',False)])
       	 	if sale_order_search != []:
       	 		 raise osv.except_osv(_('Information!'),_("Quotation is already Created for this Customer.Please use the existing Quotation which is 'SO0%s' for adding change request details") % (sale_order_search[0]))
       	 	else:
       	 		quotation_id = sale_order_obj.create(cr,uid,sale_order_value,context=context)
       	 		return {
       	 	    	'name': _('Quotations'),
       	 	    	'view_type': 'form',
       	 	    	'view_mode': 'form',
       	 	    	'view_id': [res_id],
       	 	    	'res_model': 'sale.order',
       	 	    	'type': 'ir.actions.act_window',
       	 	    	'nodestroy': True,
       	 	    	'target': 'current',
       	 	    	'res_id': quotation_id ,
       	 		}
       	else:
       		return {
       	 	    'name': _('Quotations'),
       	 	    'view_type': 'form',
       	 	    'view_mode': 'form',
       	 	    'view_id': [res_id],
       	 	    'res_model': 'sale.order',
       	 	    'type': 'ir.actions.act_window',
       	 	    'nodestroy': True,
       	 	    'target': 'current',
       	 	    
       	 	}



class sale_order(osv.osv):
	_inherit = "sale.order"

	_columns ={
		'change_request_type':fields.selection([
            ('CR', 'Change Request'),
            ('Project', 'Project'),
            ], 'Change Request', readonly=True, copy=False, help="Show Sale order is used for change request or for project", select=True),
	}

	_defaults = {
		'change_request_type':'Project',
	}

	def write(self, cr, uid, ids, vals, context=None):
		account_obj = self.pool.get('account.invoice')
		project_obj = self.pool.get('project.project')
		project_cr_obj = self.pool.get('project.change.request')
		product_obj = self.pool.get('product.product')

		order_id = self.browse(cr,uid,ids,context=context)
		if order_id.change_request_type == 'CR' and 'order_line' in vals:
			analytic_id = order_id.project_id.id
			if 'project_id' in vals:
				analytic_id = vals['project_id']
			project_id_sale = project_obj.search(cr, uid, [('analytic_account_id','=',analytic_id)])
			if project_id_sale != []:
				vals_for_cr = {
						'project_id':project_id_sale[0],
						'related_sale_order':order_id.id,
        				'customer_id': order_id.partner_id.id,
        				'user_ids': order_id.user_id.id,
				}
				for lines in vals['order_line']:
					if lines[2] != False:
						product_name = product_obj.browse(cr, uid, lines[2]['product_id'],context=context).name_template
						vals_for_cr.update({'name':product_name,'description':lines[2]['name']})
						project_cr_obj.create(cr,uid,vals_for_cr,context=context)
		res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
		if 'change_request_type' in vals:
			sale_order_det = self.browse(cr,uid,ids,context=context)
			account_obj_search = account_obj.search(cr,uid,[('origin','=',sale_order_det.name)])
			if account_obj_search != []:
				for account_record in account_obj_search:
					account_obj.write(cr, uid, account_record, {'change_request_type':sale_order_det.change_request_type})
		return res

	def open_project_form(self, cr, uid, ids, context=None):
		""" open a view on one of the given invoice_ids """
		ir_model_data = self.pool.get('ir.model.data')
		form_res = ir_model_data.get_object_reference(cr, uid, 'autmate_project_creation', 'project_creation_form_sale')
		form_id = form_res and form_res[1] or False
		if 'change_request_type' in context and context['change_request_type'] == 'CR':
			raise osv.except_osv(_('Information!'),_("This Quotation is already used for Change Request. \n Create new Quotation to create Project."))
		else:
			return {
				'name': _('Add Project'),
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'project.project',
				'view_id': [form_id],
				'type': 'ir.actions.act_window',
				'nodestroy': True,
				'target': 'current',
				'context':context,
			}


class account_invoice(osv.osv):
	_inherit = "account.invoice"
	_columns = {
		'change_request_type' :fields.selection([
            ('CR', 'Change Request'),
            ('Project', 'Project'),
            ], string='Change Request', readonly=True, copy=False, help="Show Sale order is used for change request or for project", select=True),
	}

	