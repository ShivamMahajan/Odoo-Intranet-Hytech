from openerp.osv import fields, osv
from datetime import date
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

class hr_announcement(osv.osv):
	_name = 'hr.announcement'
	_description = "Company Announcement"
	
	_columns ={
		'name':fields.char('Announcement Title', required=True),
		'message':fields.char("Annoucement Details", required=True, help="You can also use a Raw html in this box"),
		'email_notifier':fields.boolean('Notify All Employee', help="Check this box if you want to notify this announcement to all employee"),
		'date_created':fields.date("Announcement date", readonly=True),
		#'email_address':fields.char("Email Address", help="Specify email address which is used to send mail"),
	}
	_defaults = {
		'date_created': date.today().strftime('%Y-%m-%d'),
		'email_notifier':True,
	}
	_order = 'date_created desc, id desc'

	def create(self, cr, uid, values, context=None):
		hr_obj = self.pool.get('hr.employee')
		hr_employee_record = hr_obj.search(cr, uid, [('active', '=', True),('id','!=',1)], context=context)
		irconfig_obj = self.pool['ir.config_parameter']
		announcement_email = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.announcement.email')
		recipients=[]
		if values['email_notifier']== True:
			for employee in hr_obj.browse(cr,uid,hr_employee_record):
				if employee.work_email:
					vals = {'state': 'outgoing',
							'subject': values['name'],
							'body_html': values['message'],
							'email_to': employee.work_email,
							'email_from': announcement_email}
					self.pool.get('mail.mail').create(cr, uid, vals, context=context)

		return super(hr_announcement, self).create(cr, uid, values, context=context)