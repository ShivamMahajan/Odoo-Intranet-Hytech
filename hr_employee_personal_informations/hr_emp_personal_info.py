from openerp.osv import fields,osv

class hr_employee_personal_info (osv.osv):
	_name = "hr.employee.personal_info"
	_order = 'name'

	_columns = {
		###########Fields For Hr Setting############
		'previous_employer': fields.char("Previous Employer",help="Enter the employee Previous Employer Name"),
		#'employee_qualification':fields.many2one("hr.recruitment.degree", "Qualification",select=True),
		'ppercentage_score':fields.float("Percentage"),
		'pemployee_college': fields.many2one("hr.employee.instituation", "University", select=True),
		'pqualification_type':fields.many2one("hr.employee.qualification", "Qualification Type", select=True),
		'pyear_of_passing':fields.char("Year of Passing"),
		'gpercentage_score':fields.float("Percentage"),
		'gemployee_college': fields.many2one("hr.employee.instituation", "University", select=True),
		'gqualification_type':fields.many2one("hr.employee.qualification", "Qualification Type", select=True),
		'gyear_of_passing':fields.char("Year of Passing"),
		'employee_status':fields.selection([('probationary','Probationary'),('confirmed','Confirmed'),('resigned','Resigned')],'Employee Status', select=True),
		'employee_ctc':fields.float("Current CTC (in Lakhs)"),
		#################Fields For Personal Information Tab
		'name':fields.char("Employee Name", required=True),
		'work_email':fields.char("Work Email", required=True),
		'user_id':fields.many2one('res.users', 'Related Users'),
		'phone_landline':fields.char("Phone Number"),
		'self_mobile':fields.char("Personal Mobile No."),
		'mobile_alternative':fields.char("Mobile (Alternative)"),
		'corrospondence_address': fields.text('Corrospondence Address'),
        'permanent_address': fields.text('Permanent Address'),
        'permanent_pin':fields.char("Pin Code"),
        'blood_group':fields.char("Blood Group"),
        'father_name':fields.char("Father Name"),
    	'pan_number':fields.char("PAN Number"),
    	'personal_email_id':fields.char("Personal Email ID"),
        'spouse_name':fields.char("Spouse Name "),
        'anniversary_date':fields.date("Aniversary Date"),
        'other_qualification':fields.char("Other Qualification /Certifications"),
        'technical_expertise':fields.char("Technical Expertise"),
        'country_id': fields.many2one('res.country', 'Nationality'),
        'date_of_joining':fields.date("Date of Joining"),
        'identification_id': fields.char('Employee ID'),
        'passport_id': fields.char('Passport No'),
        'otherid': fields.char('Other Id'),
        'gender': fields.selection([('male', 'Male'), ('female', 'Female')], 'Gender'),
        'marital': fields.selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Marital Status'),
        'active':fields.boolean("Active"),
        'birthday': fields.date("Date of Birth"),

	}

	_defaults = {
	 	'ppercentage_score': 0.0,
	 	'gpercentage_score': 0.0,
	 	'employee_ctc':0.0,
	 	'active': True,
	}
	_sql_constraints = [
		 ('work_email_uniq', 'unique(work_email)', 'The Working Email ID must be unique per employee'),
	]

	def create(self, cr, uid, data, context=None):	
		
		return super(hr_employee_personal_info, self).create(cr, uid, data, context=context)

	def write(self, cr, uid, ids, vals, context=None):

		return super(hr_employee_personal_info, self).write(cr, uid, ids, vals, context=context)