from openerp.osv import fields, osv
from openerp.tools.translate import _


class hr_evaluation_interview(osv.Model):
    _inherit = 'hr.evaluation.interview'
    
    _columns ={
    	'appraisal_rating_ids':fields.one2many('hr_evaluation.parameter.rating', 'interview_extends_id', 'Parameter Rating'),
    }

class hr_evaluation_parameter_rating(osv.osv):
	_name ="hr_evaluation.parameter.rating"
	_desriptions= "Appraisal Rating"

	_columns = {
		'name':fields.char("Parameter name",required=True),
		'appraisee_rating': fields.float("Appraisee Rating",group_operator="avg"),
		'appraiser_rating': fields.float("Appraiser Rating", group_operator="avg"),
		'evaluation_extends_id': fields.many2one('hr_evaluation.evaluation', "Evaluation Name"),
		'interview_extends_id': fields.many2one('hr.evaluation.interview', "Interview Name"),
		'appraisal_plan_id': fields.many2one('hr_evaluation.plan',"Plan Name"),
		'cycle_type':fields.selection([('cycle1','Cycle 1'),('cycle2','Cycle 2')],"Cycle Type"),
		'date_from':fields.date("Period Start"),
		'date_to':fields.date("Period End"),
		'employee_id':fields.many2one('hr.employee', "Employee Name"),
		'user_id': fields.many2one('res.users', "Related User"),
		'date':fields.date("Creation Date"),
		'manager': fields.many2one('hr.employee', 'Manager'),
        'company_id': fields.many2one('res.company', 'Company'),
        'appraisee_comment': fields.text('Appraisee Comment'),
        'appraiser_comment': fields.text('Appraiser Comment'),
	}

	# def unlink(self, cr, uid, ids, context=None):
	# 	for rec in self.browse(cr, uid, ids, context=context):
	# 		raise osv.except_osv(_('Warning!'),_('You are not allowed to delete a Appraisal Rating Records.'))
	# 	return super(hr_evaluation_parameter_rating, self).unlink(cr, uid, ids, context)

class hr_employee(osv.Model):
	_inherit="hr.employee"


	def generate_appraisal_form(self, cr, uid, ids, context=None):
		obj_evaluation = self.pool.get('hr_evaluation.evaluation')
		for emp in self.browse(cr, uid, ids, context=context):
			if emp.evaluation_plan_id.id != False:
				plan_id = obj_evaluation.create(cr, uid, {'employee_id': emp.id, 'plan_id': emp.evaluation_plan_id.id,'manager':emp.parent_id.id,'company_id':emp.company_id.id}, context=context)
				interview_boolean = obj_evaluation.button_plan_in_progress(cr, uid, [plan_id], context=context)
		return True