from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_evaluation_resend_reason(osv.osv_memory):
	_name = 'hr.evaluation.resend.reason'
	_description = ' Manager Reasons for Resending Approval'
	_columns = {
		'reason_for_resend':fields.text('Reason for Resending',required=True),
	}

	def action_resend_appraisal(self, cr, uid, ids, context=None):
		context = dict(context or {})
		reason_for_resend_test=self.browse(cr,uid,ids).reason_for_resend
		interview_obj=self.pool.get("hr.evaluation.interview")
		interview = interview_obj.browse(cr, uid, context['active_id'], context=context)[0]
		response_obj = self.pool.get('survey.user_input')
		# grab the token of the response
		response = response_obj.browse(cr, uid, interview.request_id.id, context=context)
		if reason_for_resend_test != False:
			response_obj.write(cr,uid,[response.id],{'state':'new','last_displayed_page_id':'','write_uid':interview.evaluation_id.employee_id.user_id.id},context=context)
			if interview.evaluation_id.employee_id.parent_id.work_email and interview.evaluation_id.employee_id.work_email:
				body =('''<p>This is to inform you that your Project Manager is not satisfy by your Appraisal Form submitted.\n <b>Below the Reasons Specified by your manager:</b> \n %s \n<b>In case any query contact your Project Manager </b> </p>''')%reason_for_resend_test
				vals = {
					'state': 'outgoing',
					'subject': 'Verification Needed on your Appraisal Form',
					'body_html': '<pre>%s</pre>' % body,
					'email_to': interview.evaluation_id.employee_id.work_email,
					'email_from': interview.evaluation_id.employee_id.parent_id.work_email}
				self.pool.get('mail.mail').create(cr, uid, vals, context=context)
				interview_obj.write(cr,uid,[interview.id],{'state':'resend'})
		else:
			raise osv.except_osv(_('Warning!'), _("Please provide some Reasons before resending this form back to your suboridnate."))
		return True    
