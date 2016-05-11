from openerp.osv import fields,osv

class hr_employee (osv.osv):
	_inherit = "hr.employee"
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
		'phone_landline':fields.char("Phone Number"),
		'self_mobile':fields.char("Personal Mobile No."),
		'mobile_alternative':fields.char("Mobile (Alternative)"),
		'corrospondence_address': fields.text('Corrospondence Address'),
        'permanent_address': fields.text('Permanent Address'),
        'permanent_pin':fields.char("Pin Code"),
        'blood_group':fields.char("Blood Group"),
        'father_name':fields.char("Father Name"),
       # 'relative_name':fields.char("Relative Name "),
       # 'relative_mobile':fields.char("Relative Mobile No. "),
    	'pan_number':fields.char("PAN Number"),
    	'personal_email_id':fields.char("Personal Email ID"),
        'spouse_name':fields.char("Spouse Name "),
        'anniversary_date':fields.date("Aniversary Date"),
        'technical_expertise':fields.char("Technical Expertise"),
        'other_qualification':fields.char("Other Qualification /Certifications"),
        'otherid': fields.char('Other Id'),
        'birthday': fields.date("Date of Birth"),
        ######key skills Field ###########
        'key_skill':fields.many2many('skillset.skillset','employee_skillset_rel', 'employee_id', 'record_id', 'Key Skills'),

	}

	_defaults = {
	 	'ppercentage_score': 0.0,
	 	'gpercentage_score': 0.0,
	 	'employee_ctc':0.0,
	}

	
	def create(self, cr, uid, data, context=None):
		hr_employee_personal_info_obj = self.pool.get('hr.employee.personal_info')
		if 'work_email' in data:
			hr_employee_personal_search = hr_employee_personal_info_obj.search(cr, uid, [('work_email','=',data['work_email']),('active','=',True)])
			if hr_employee_personal_search == []:
				hr_employee_personal_info_obj.create(cr, uid, data, context=context)
		return super(hr_employee, self).create(cr, uid, data, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		hr_employee_personal_info_obj = self.pool.get('hr.employee.personal_info')
		change_info_id_new = self.browse(cr,uid,ids,context)
		val_for_hr_personal_tab={}
		hr_employee_personal_search = hr_employee_personal_info_obj.search(cr, uid, [('work_email','=',change_info_id_new.work_email)])
		if 'country_id' in vals:
			val_for_hr_personal_tab.update({'country_id': vals['country_id']})
		if 'date_of_joining' in vals:
			val_for_hr_personal_tab.update({'date_of_joining': vals['date_of_joining']})
		if 'identification_id' in vals:
			val_for_hr_personal_tab.update({'identification_id': vals['identification_id']})
		if 'passport_id' in vals:
			val_for_hr_personal_tab.update({'passport_id': vals['passport_id']})
		if 'otherid' in vals:
			val_for_hr_personal_tab.update({'otherid': vals['otherid']})
		if 'pan_number' in vals:
			val_for_hr_personal_tab.update({'pan_number': vals['pan_number']})
		if 'personal_email_id' in vals:
			val_for_hr_personal_tab.update({'personal_email_id': vals['personal_email_id']})
		if 'phone_landline' in vals:
			val_for_hr_personal_tab.update({'phone_landline': vals['phone_landline']})
		if 'self_mobile' in vals:
			val_for_hr_personal_tab.update({'self_mobile': vals['self_mobile']})
		if 'mobile_alternative' in vals:
			val_for_hr_personal_tab.update({'mobile_alternative': vals['mobile_alternative']})
		if 'corrospondence_address' in vals:
			val_for_hr_personal_tab.update({'corrospondence_address': vals['corrospondence_address']})
		if 'permanent_address' in vals:
			val_for_hr_personal_tab.update({'permanent_address': vals['permanent_address']})
		if 'permanent_pin' in vals:
			val_for_hr_personal_tab.update({'permanent_pin': vals['permanent_pin']})
		if 'gender' in vals:
			val_for_hr_personal_tab.update({'gender': vals['gender']})
		if 'marital' in vals:
			val_for_hr_personal_tab.update({'marital': vals['marital']})
		if 'spouse_name' in vals:
			val_for_hr_personal_tab.update({'spouse_name': vals['spouse_name']})
		if 'anniversary_date' in vals:
			val_for_hr_personal_tab.update({'anniversary_date': vals['anniversary_date']})
		if 'blood_group' in vals:
			val_for_hr_personal_tab.update({'blood_group': vals['blood_group']})
		if 'father_name' in vals:
			val_for_hr_personal_tab.update({'father_name': vals['father_name']})
		if 'ppercentage_score' in vals:
			val_for_hr_personal_tab.update({'ppercentage_score': vals['ppercentage_score']})
		if 'pemployee_college' in vals:
			val_for_hr_personal_tab.update({'pemployee_college': vals['pemployee_college']})
		if 'pqualification_type' in vals:
			val_for_hr_personal_tab.update({'pqualification_type': vals['pqualification_type']})
		if 'pyear_of_passing' in vals:
			val_for_hr_personal_tab.update({'pyear_of_passing': vals['pyear_of_passing']})
		if 'gpercentage_score' in vals:
			val_for_hr_personal_tab.update({'gpercentage_score': vals['gpercentage_score']})
		if 'gemployee_college' in vals:
			val_for_hr_personal_tab.update({'gemployee_college': vals['gemployee_college']})
		if 'gqualification_type' in vals:
			val_for_hr_personal_tab.update({'gqualification_type': vals['gqualification_type']})
		if 'gyear_of_passing' in vals:
			val_for_hr_personal_tab.update({'gyear_of_passing': vals['gyear_of_passing']})
		if 'previous_employer' in vals:
			val_for_hr_personal_tab.update({'previous_employer': vals['previous_employer']})
		if 'other_qualification' in vals:
			val_for_hr_personal_tab.update({'other_qualification': vals['other_qualification']})
		if 'technical_expertise' in vals:
			val_for_hr_personal_tab.update({'technical_expertise': vals['technical_expertise']})
		if 'birthday' in vals:
			val_for_hr_personal_tab.update({'birthday': vals['birthday']})

		if hr_employee_personal_search == []:
			personal_data={
				'name':change_info_id_new.name,
				'work_email':change_info_id_new.work_email,
				'user_id':change_info_id_new.user_id.id,
			}
			hr_personal_info_id = hr_employee_personal_info_obj.create(cr, uid, personal_data, context=context)
			hr_employee_personal_info_obj.write(cr, uid, hr_personal_info_id, val_for_hr_personal_tab, context=context)
		else:
			hr_employee_personal_browse = hr_employee_personal_info_obj.browse(cr,uid,hr_employee_personal_search, context=context )
			hr_employee_personal_info_obj.write(cr, uid, hr_employee_personal_browse.id, val_for_hr_personal_tab, context=context)
		print ("Employee Extends"),super(hr_employee, self).write(cr, uid, ids, vals, context=context)
		return super(hr_employee, self).write(cr, uid, ids, vals, context=context)

	def run_fetch_employee_image_from_users(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
		users_object = self.pool.get("res.users")
		users_object_search = users_object.search(cr,uid,[('active','=',True),('image','!=',False)])
		for users_record in users_object.browse(cr,uid,users_object_search):
			related_employee = self.search(cr,uid,[('active','=',True),('user_id','=',users_record.id),('image','=',False)])
			if related_employee != []:
				self.write(cr,uid,related_employee,{'image':users_record.image,'image_medium':users_record.image,'image_small':users_record.image})
		return True

	

class hr_employee_instituation(osv.osv):
	_name = "hr.employee.instituation"
	_description = "Employee College/Instituation"
	_columns = {
		'name':fields.char("College Name", required=True),
	}

	_sql_constraints = [
		 ('name_uniq', 'unique(name)', 'The name of College Must be unique'),
	]

class hr_employee_qualification(osv.osv):
	_name = "hr.employee.qualification"
	_description = "Employee Qualification"
	_columns = {
		'name':fields.char("Qualification Name", required=True),
	}

	_sql_constraints = [
		 ('name_uniq', 'unique(name)', 'The name of Qualification Must be unique'),
	]