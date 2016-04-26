from openerp.osv import fields, osv
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import math
import time
from operator import attrgetter
from openerp.exceptions import Warning
from openerp import tools
from openerp import SUPERUSER_ID


class hr_holidays(osv.osv):
	_inherit = "hr.holidays"

	# TODO: can be improved using resource calendar method
	def _get_number_of_days(self, date_from, date_to):
		"""Returns a float equals to the timedelta between two dates given as string."""

		DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
		from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
		to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
		timedelta = to_dt - from_dt
		days_included = 0.0
		for diff in range(0,timedelta.days+1):
			next_date= from_dt + relativedelta(days=diff)
			if from_dt == next_date :
				days_included = 0.0
			elif next_date.strftime('%a') == 'Sat' or next_date.strftime('%a') == 'Sun':
				pass
			else:
				days_included += 1.0
		diff_day = timedelta.days + float(timedelta.seconds) / 86400
		return days_included


	_columns= {
		'reasons_comment':fields.text('Reasons For Approval',),
		'number_of_days_temp': fields.float('Allocation', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}, copy=False),
		'state_value':fields.char("Status Value"),
		####### New Fields added as per New Enhancement ####
		'carry_forward':fields.integer("Carry Forwarded (in days)", readonly=True, help="Enter number of leaves which is carry forwarded from previous year",states={'draft':[('readonly',False)], 'confirm':[('readonly',False)],'validate1':[('readonly',False)]}),
		'allocated_number':fields.integer("Current Allocated (in days)", readonly=True, help="Enter number of leaves which is allocated this year", states={'draft':[('readonly',False)], 'confirm':[('readonly',False)],'validate1':[('readonly',False)]}),
		####Total available leave ###
		'total_available_leave': fields.integer("Available leave"),
		'sub_total_available_leave':fields.integer("Sub Available leave",readonly=True),
		##### Advance leave applied for ###
		'advanced_leave': fields.selection([('yes','Yes'),('no','No')], string="Include Advance Leave", readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}, copy=False),
		'advanced_leave_unit':fields.float("Advance leave(Max 4 days)"),
		'sub_advanced_leave_unit':fields.integer("Sub Advance leave",readonly=True),
		#### Check leave Applied in a Salary Month 
		'is_leave_more':fields.boolean("Is Taken More than 5 in salary month"),
		'extra_leave_applied':fields.integer("Extra Leave applied in a Salary month"),
		'sub_extra_leave_applied':fields.integer("Sub Extra Leave applied in a Salary month",readonly=True),
		####### Define Effective Period of Allocation
		'leave_allocate_year_start':fields.date("Effected From",readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}, copy=False),
		'leave_allocate_year_end':fields.date("Effected To",readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}, copy=False),
		'record_leave_year':fields.char("Current Year"),
		'is_el':fields.boolean("Is EL"),
        'is_cl':fields.boolean("Is CL"),
        'is_unpaid':fields.boolean("Is Unpaid"),
        ###########Sandwich Check############
        'is_sandwich':fields.boolean("Is Sandwich"),
        'sandwich_days':fields.integer("Extra Sandwich Days"),
        ###########Applied leave validation fields
        'actual_num_temp_day':fields.float("Actual Number of days Applied"),
        
	}
	
	_defaults ={
		'date_from': lambda *a: datetime.datetime.now().replace(hour=7, minute=0, second=0),
		'advanced_leave' : 'no',
		'leave_allocate_year_start': lambda *a: (datetime.datetime.now()).replace(day=1,month=1).strftime("%Y-%m-%d"),
		'leave_allocate_year_end': lambda *a: (datetime.datetime.now()).replace(day=31,month=12).strftime("%Y-%m-%d"),
		'carry_forward':0,
		'allocated_number':0,
		'advanced_leave_unit':0.0,
		'number_of_days_temp':0.0,
		'record_leave_year': lambda *a: datetime.datetime.now().strftime('%Y'),
		
	}

	def onchange_leave_type(self,cr,uid,ids,leave_type):
		result = {'domain': {}}
		leave_type_obj = self.pool.get("hr.holidays.status")
		leave_type_search = leave_type_obj.search(cr,uid,['|',('is_el','=',True),('is_cl','=',True)])
		if leave_type == 'add':
			result['domain']['holiday_status_id']=[('id', 'in', leave_type_search)]
		return result	
	
	def get_company_id_apply_leave_policy(self,cr,uid,ids,context=None):
		users_obj=self.pool.get("res.users")
		user_list=users_obj.search(cr,uid,[('id','=',uid)])
		user_recordset=users_obj.browse(cr,uid,user_list)
		company_obj=self.pool.get('res.company')
		company_id=company_obj.search(cr,uid,[('id','=',user_recordset.company_id.id),('apply_leave_policy','=',True)])
		# company_record_set=company_obj.browse(cr,uid,company_id)
		return company_id


	def validate_leave_policy(self, cr, uid, ids,date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp, context=None):
		result = {'value': {}}
		result['value']['number_of_days_temp']=number_of_days_temp
		result['value']['actual_num_temp_day']=number_of_days_temp
		#############Verifying Check in dates 
		# date_to has to be greater than date_from
		if (date_from and date_to) and (date_from > date_to):
			raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

		# Compute and update the number of days
		if (date_to and date_from) and (date_from <= date_to):
			diff_day = self._get_number_of_days(date_from, date_to)
			result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
			result['value']['actual_num_temp_day']=round(math.floor(diff_day))+1
			
		else:
			result['value']['number_of_days_temp'] = 0
			result['value']['actual_num_temp_day']=0
			

		company_id_leave_policy=self.get_company_id_apply_leave_policy(cr,uid,ids,context=None)
		employee_object = self.pool.get('hr.employee')
		employee_id_search=employee_object.search(cr,uid,[('id','=',employee_id),('active','=',True)])
		now = datetime.datetime.now()
		mechanism_day_allocated = 0
		carry_forward_days=0
		# leave_taken_so_far = 0
		month_list = [1,2,3,4,5,6,7,8,9,10,11,12]
			
		date_to_value = date_to
		if not date_to:
			date_to_value = date_from

		start_date = (datetime.datetime.now()).replace(day=1,month=1).strftime("%Y-%m-%d")
		end_date = (datetime.datetime.now()).replace(day=31,month=12).strftime("%Y-%m-%d")
		leave_mechanism_line_obj = self.pool.get('leave.mechanism.line')
		date_from_format = datetime.datetime.strptime(date_from,"%Y-%m-%d %H:%M:%S")
		date_to_format = datetime.datetime.strptime(date_to_value,"%Y-%m-%d %H:%M:%S")
		months_taken_from_list = month_list[0:date_to_format.month]


		if holiday_status_id:
			applied_leave_type_obj = self.pool.get("hr.holidays.status")
			applied_leave_type = applied_leave_type_obj.browse(cr,uid,holiday_status_id)
			
			if company_id_leave_policy :
				if applied_leave_type.is_el==True:
					result['value']['is_el']= True
					result['value']['is_cl']= False
					result['value']['is_unpaid']= False
					
				elif applied_leave_type.is_cl==True:
					result['value']['is_cl']= True
					result['value']['is_el']= False
					result['value']['is_unpaid']= False
				
				elif applied_leave_type.is_unpaid==True:
					result['value']['is_unpaid']= True
					result['value']['is_el']= False
					result['value']['is_cl']= False
					

				
			# Approved leaves
			allocation_ids = self.search(cr, uid, [('employee_id', '=', employee_id),
	                                                                ('state', '=','validate'),
	                                                                ('type','=','add'),
	                                                                ('holiday_status_id', '=', holiday_status_id),
	                                                               	('leave_allocate_year_start','>=',start_date),
	                                                               	('leave_allocate_year_end','<=', end_date)])
	        

	        ####### To Know Carry forwar leave Unit                                                       	
			if len(allocation_ids) == 1:
				carry_forward_days = self.browse(cr,uid, allocation_ids).carry_forward

			# Calculate all the leave applied including To approve ,Second Approval,Approved
			leave_allocation_ids_remove = self.search(cr, uid, [('employee_id', '=', employee_id),
	                                                                ('state', 'in',['confirm', 'validate','validate1']),
	                                                                ('type','=','remove'),
	                                                                ('holiday_status_id', '=', holiday_status_id),
	                                                               	('leave_allocate_year_start','>=',start_date),
	                                                               	('leave_allocate_year_end','<=', end_date),
	                                                               	('id','!=',ids)])
			

			total_out_of_allocated_taken=0
			for i in leave_allocation_ids_remove :
				total_out_of_allocated_taken+=self.browse(cr,uid,i).number_of_days_temp
				
							##### Allowed Leave according to Leave Mechanism
		 	# Check Whether the EL and CL is approved or not so that mechanism chart should be followed
			
			if applied_leave_type.is_el==True or applied_leave_type.is_cl==True:
				if allocation_ids :
					# if total_out_of_allocated_taken <= self.browse(cr,uid, allocation_ids).number_of_days_temp:
						if company_id_leave_policy:
							leave_mechanism_line_search = leave_mechanism_line_obj.search(cr,uid,[('year_value','in',months_taken_from_list)])
							if applied_leave_type.is_el == True:
									for leave_mechanism_line_EL in leave_mechanism_line_obj.browse(cr,uid,leave_mechanism_line_search):
										mechanism_day_allocated += leave_mechanism_line_EL.subjected_el
									

							if 	applied_leave_type.is_cl == True:
									for leave_mechanism_line_cl in leave_mechanism_line_obj.browse(cr,uid,leave_mechanism_line_search):
										mechanism_day_allocated += leave_mechanism_line_cl.subjected_cl
							
							if (carry_forward_days + mechanism_day_allocated - total_out_of_allocated_taken) <self.browse(cr,uid, allocation_ids).number_of_days_temp :
								result['value']['total_available_leave'] = (carry_forward_days + mechanism_day_allocated) - total_out_of_allocated_taken
								result['value']['sub_total_available_leave'] = (carry_forward_days + mechanism_day_allocated) - total_out_of_allocated_taken
							else :
								result['value']['total_available_leave'] = self.browse(cr,uid, allocation_ids).number_of_days_temp - total_out_of_allocated_taken
								result['value']['sub_total_available_leave'] = self.browse(cr,uid, allocation_ids).number_of_days_temp - total_out_of_allocated_taken
								
						else :
							result['value']['total_available_leave'] = self.browse(cr,uid, allocation_ids).number_of_days_temp  - total_out_of_allocated_taken
							result['value']['sub_total_available_leave'] = self.browse(cr,uid, allocation_ids).number_of_days_temp - total_out_of_allocated_taken
				else :
					result['value']['total_available_leave'] = 0.0
					result['value']['sub_total_available_leave'] = 0.0
					
						
			if applied_leave_type.is_unpaid==True :
				result['value']['total_available_leave'] =result['value']['number_of_days_temp']
			

				######## Check In case for Privilege Leave
			if len(employee_id_search)==1 and applied_leave_type.limit == True :
				if applied_leave_type.is_unpaid ==False:
					employee_browse = employee_object.browse(cr,uid,employee_id_search)
					employee_joining = employee_browse.date_of_joining
					if company_id_leave_policy:
						if employee_joining:
							employee_joining_format=datetime.datetime.strptime(employee_joining + " " + "00:00:00","%Y-%m-%d %H:%M:%S")
							diff_in_year = relativedelta(now, employee_joining_format)
							new_diff = float(str(diff_in_year.years) + '.' + str(diff_in_year.months))
							if new_diff >= applied_leave_type.year_value:
								result['value']['total_available_leave'] = applied_leave_type.leave_limit
								result['value']['sub_total_available_leave']=applied_leave_type.leave_limit
							else:
								raise Warning(_('You are not eligible for this leave type'))
						else:
							raise Warning(_('Please Enter Joining date in Employee Form.'))
					else :
						result['value']['total_available_leave'] = applied_leave_type.leave_limit
						result['value']['sub_total_available_leave']=applied_leave_type.leave_limit

			
			##### Check Total number of leave taken in Salary Month
		leave_taken_salary_month = 0
		extra_leave_taken_month = 0
		start_salary_month=''
		if date_to_format.month-1 == 0:
			start_salary_month = date_to_format.replace(day=26,month=12,year=date_to_format.year-1,hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
		else:
			start_salary_month = date_to_format.replace(day=26,month=date_to_format.month-1,hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")

		end_salary_month = date_to_format.replace(day=25,hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
			
			############total number of Leave in Salary month
		leave_salary_month_ids = self.search(cr, uid, [('employee_id', '=', employee_id),
	                                                                ('state', 'in',['validate','validate1']),
	                                                                ('type','=','remove'),
	                                                               	('date_from','>=',start_salary_month),
	                                                               	('date_to','<=', end_salary_month)])
		for leave_salary_browse in self.browse(cr, uid,leave_salary_month_ids ):
				leave_taken_salary_month += leave_salary_browse.number_of_days_temp
				extra_leave_taken_month += leave_salary_browse.extra_leave_applied

		total_needed_right_now = (leave_taken_salary_month + result['value']['number_of_days_temp'])- extra_leave_taken_month
			
		if company_id_leave_policy:
			if total_needed_right_now > 5:
				result['value']['is_leave_more'] = True
				number_of_time = int(total_needed_right_now/5)
				added_value = 0 
				if total_needed_right_now % 5 == 0:
					if int(extra_leave_taken_month/2) % 2 == 0:
						added_value = 2 * (number_of_time-1) 
				else:
					if int(extra_leave_taken_month/2) % 2 == 0 or  total_needed_right_now > 10:
						if result['value']['number_of_days_temp'] != total_needed_right_now:
							added_value = 2 
						else:
							added_value = 2 * number_of_time
				result['value']['extra_leave_applied'] = added_value
				result['value']['sub_extra_leave_applied'] = added_value
			else:
				result['value']['is_leave_more'] = False
				result['value']['extra_leave_applied'] = 0.0
				result['value']['sub_extra_leave_applied'] = 0.0
		else:
			result['value']['is_leave_more'] = False
			result['value']['extra_leave_applied'] = 0.0
			result['value']['sub_extra_leave_applied'] = 0.0


			##################Check Sandwich##########
		if company_id_leave_policy :
			date_from_sandwich = datetime.datetime.strptime(date_from,"%Y-%m-%d %H:%M:%S")
			date_previous_day = date_from_sandwich - datetime.timedelta(days=1)
			public_holiday_obj= self.pool.get("company.public.holidays")
			public_holiday_search = public_holiday_obj.search(cr,uid,[('holiday_day','=',str(date_previous_day).split(" ")[0])])
			if public_holiday_search != []:
				second_next=date_from_sandwich - datetime.timedelta(days=2)
				sandwich_leave=self.search(cr,uid,[('type','=','remove'),('date_to','>=',str(second_next))])
				if sandwich_leave != []:
					result['value']['is_sandwich']= True
					result['value']['sandwich_days']= 1 
				else:
					result['value']['is_sandwich']= False
					result['value']['sandwich_days']= 0
		else:
			result['value']['is_sandwich']= False
			result['value']['sandwich_days']= 0
		
				
		return result

	def onchange_date_from(self, cr, uid, ids, date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp,context=None):
		"""
		If there are no date set for date_to, automatically set one 8 hours later than
		the date_from.
		Also update the number_of_days.
		# """
		result = {'value': {}}
		result=self.validate_leave_policy(cr, uid, ids,date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp, context=None)
		if date_from and not date_to:
			date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
			result['value']['date_to'] = str(date_to_with_delta)
		return result


	def onchange_date_to(self, cr, uid, ids, date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp,context=None):
		"""
		Update the number_of_days.
		"""
		result = {'value': {}}
		result=self.validate_leave_policy(cr, uid, ids,date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp, context=None)
		return result
		
	### Onchange For Carry forward and Alocated Leave ###
	def onchange_carry_and_allocate(self, cr, uid, ids, carry_forward, allocated_number):
		result = {'value': {}}
		if carry_forward or allocated_number :
			result['value']['number_of_days_temp'] = carry_forward + allocated_number
		return result

	def create(self, cr, uid, values, context=None):
		""" Override to avoid automatic logging of creation """
		if context is None:
			context = {}
		context = dict(context, mail_create_nolog=True)
		extra_value={'sub_total_available_leave':0,'sub_advanced_leave_unit':0,'sub_extra_leave_applied':0}
		##### creating half day leave
		if values['type'] =='remove':
			applied_leave_type_obj = self.pool.get("hr.holidays.status")
			applied_leave_type = applied_leave_type_obj.browse(cr,uid,values.get("holiday_status_id"))
			diff_day = self._get_number_of_days(values['date_from'], values['date_to'])
			if values['number_of_days_temp'] <= round(math.floor(diff_day))+1:
				if values['number_of_days_temp'] >= (round(math.floor(diff_day))+1)-0.5:
					if str(values['number_of_days_temp']-int(values['number_of_days_temp'])) != '0':
						number_dec = str(values['number_of_days_temp']-int(values['number_of_days_temp']))[2:]
						if int(number_dec) != 0:
							new_number_of_days_temp = int(values['number_of_days_temp']) + 0.5
							values['number_of_days_temp']=new_number_of_days_temp
							values['actual_num_temp_day']=new_number_of_days_temp
					values['number_of_days_temp'] = values['number_of_days_temp']
					values['actual_num_temp_day'] = values['actual_num_temp_day']
				else:
					raise osv.except_osv(_('Warning!'),_('Selected duration is for %s days.So you have to take leave more than %s or equal to duration.')%(round(math.floor(diff_day))+1,values['number_of_days_temp']))
			else:
				raise osv.except_osv(_('Warning!'),_('Please verify your leave number of days with duration which you have enter above.'))

			##### Check Earned Leave not applied for Past date
			if 'date_from' in values:
				date_from_new = values.get('date_from').split(' ')[0]
				today= datetime.datetime.now()
				new_today = str(today).split(' ')[0]
				if (date_from_new < new_today):
					if applied_leave_type.is_el == True:
						raise Warning(_('You are not allowed to take Earned Leave for Past Date.'))

			##### Check Total leave available + Advance Leave
			if 	'total_available_leave' in values:
				extra_value['sub_total_available_leave']=values.get('total_available_leave')
				if values['number_of_days_temp'] > values.get('total_available_leave'):
					raise Warning(_("You don't have enough leaves to apply" ))
			 	if values.get('advanced_leave') == 'yes':
					total_available = values.get('total_available_leave') + values.get('advanced_leave_unit')

					if values['number_of_days_temp'] > total_available:
						raise Warning(_("You don't have enough leaves to apply" ))

			#####Check extra Leave Applied for an Employee
			if 'extra_leave_applied' in values:
				extra_value['sub_extra_leave_applied']= values.get('extra_leave_applied')
				values['number_of_days_temp'] = values['number_of_days_temp'] + values.get('extra_leave_applied')
				values['actual_num_temp_day'] = values['actual_num_temp_day']+values.get('extra_leave_applied')
			###########Check Limit Defined in the not legal Leaves
			if "holiday_status_id" in values:
				if applied_leave_type.limit == True and applied_leave_type.is_unpaid==False:
					if values['number_of_days_temp'] > applied_leave_type.leave_limit:
						raise Warning(_("You are only allowed to take %s leaves." )%applied_leave_type.leave_limit)

			#####Check For sandwich
			if 'is_sandwich' in values and values['is_sandwich']==True:
				values['number_of_days_temp']=values['number_of_days_temp']+values.get('sandwich_days')
				values['actual_num_temp_day']=values['actual_num_temp_day']+values.get('sandwich_days')
			####leave Applied validation
			if values['number_of_days_temp'] != values['actual_num_temp_day']:
				values['number_of_days_temp']= values['actual_num_temp_day']
			values.update(extra_value)

		#############validation on allocation of leave
		if values['type'] =='add':
			start_date = (datetime.datetime.now()).replace(day=1,month=1).strftime("%Y-%m-%d")
			end_date = (datetime.datetime.now()).replace(day=31,month=12).strftime("%Y-%m-%d")
			if values['is_el'] == True:
				holidays_record = self.search(cr,uid,[('type','=','add'),('is_el','=',values['is_el']),('employee_id','=',values['employee_id']),('leave_allocate_year_start','>=',start_date),
                                                               	('leave_allocate_year_end','<=', end_date)])
				if holidays_record !=[]:
					raise Warning(_("Earned leave is already allocated to selected employee" ))
			if values['is_cl'] == True:
				holidays_record = self.search(cr,uid,[('type','=','add'),('is_cl','=',values['is_cl']),('employee_id','=',values['employee_id']),('leave_allocate_year_start','>=',start_date),
                                                               	('leave_allocate_year_end','<=', end_date)])
				if holidays_record !=[]:
					raise Warning(_("Casual leave is already allocated to selected employee" ))

			if values['number_of_days_temp'] != values['carry_forward'] + values['allocated_number']:
				raise Warning(_("Total must be equal to sum of carry forward and current allocated" ))

##################Getting Value of State To Show In calender view ##########
		if values.get('state'):
			state_dictionary = {'draft': 'In Draft','cancel': 'Cancelled','cancel_approval':'Waiting Cancel Approval','confirm': 'First Approval','refuse': 'Refused', 'validate1': 'Second Approval', 'validate':'Approved'}
			values.update({'state_value':state_dictionary[values.get('state')]})

		if values.get('state') and values['state'] not in ['draft', 'confirm', 'cancel'] and not self.pool['res.users'].has_group(cr, uid, 'base.group_hr_project_manager'):
			raise osv.except_osv(_('Warning!'), _('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
		return super(hr_holidays, self).create(cr, uid, values, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		### validating update for half day
		if len(ids)==1:
			applied_leave_type_obj = self.pool.get("hr.holidays.status")
			applied_leave_type = applied_leave_type_obj.browse(cr,uid,vals.get("holiday_status_id"))
			write_leave_obj = self.browse(cr,uid,ids)
			leave_applied_temp = write_leave_obj.number_of_days_temp
			if write_leave_obj.type == 'remove':
				############### In Past Date Not able to take Earned leave
				date_from_new = (write_leave_obj.date_from).split(' ')[0]
				today= datetime.datetime.now()
				new_today = str(today).split(' ')[0]
				if (date_from_new < new_today):
					if write_leave_obj.state in ['draft','confirm'] and 'holiday_status_id' in vals:
						if applied_leave_type.is_el== True:
							raise Warning(_('You are not allowed to take Earned Leave for Past Date.'))
				###################################
				for key in vals.keys():
					if key == 'date_to' :
						diff_day = self._get_number_of_days(write_leave_obj.date_from, vals['date_to'])
						if key == 'number_of_days_temp':
							if vals['number_of_days_temp'] <= round(math.floor(diff_day))+1:
								if vals['number_of_days_temp'] >= (round(math.floor(diff_day))+1)-0.5:
									if str(vals['number_of_days_temp']-int(vals['number_of_days_temp'])) != '0' :
										number_dec = str(vals['number_of_days_temp']-int(vals['number_of_days_temp']))[2:]
										if int(number_dec) != 0:
											new_number_of_days_temp = int(vals['number_of_days_temp']) + 0.5
											vals.update({'number_of_days_temp':new_number_of_days_temp})
											vals.update({'actual_num_temp_day':new_number_of_days_temp})
									vals.update({'number_of_days_temp':vals['number_of_days_temp']})
									vals.update({'actual_num_temp_day':vals['actual_num_temp_day']})
								else: 
									raise osv.except_osv(_('Warning!'),_('Selected duration is for %s days.So you have to take leave more than %s or equal to duration.')%(round(math.floor(diff_day))+1,vals['number_of_days_temp']))
							else:
								raise osv.except_osv(_('Warning!'),_('Please verify your leave number of days with duration which you have enter above.'))
					
					if key == 'number_of_days_temp' and len(vals) == 1:	
						diff_day = self._get_number_of_days(write_leave_obj.date_from,write_leave_obj.date_to)
						if vals['number_of_days_temp'] <= round(math.floor(diff_day))+1:
							if vals['number_of_days_temp'] >= (round(math.floor(diff_day))+1)-0.5:
								if str(vals['number_of_days_temp']-int(vals['number_of_days_temp'])) != '0' :
									number_dec = str(vals['number_of_days_temp']-int(vals['number_of_days_temp']))[2:]
									if int(number_dec) != 0:
										new_number_of_days_temp = int(vals['number_of_days_temp']) + 0.5
										vals.update({'number_of_days_temp':new_number_of_days_temp})
										if 'actual_num_temp_day' in vals:
											vals.update({'actual_num_temp_day':new_number_of_days_temp})
								vals.update({'number_of_days_temp':vals['number_of_days_temp']})
								if 'actual_num_temp_day' in vals:
									vals.update({'actual_num_temp_day':vals['actual_num_temp_day']})
							else :
								raise osv.except_osv(_('Warning!'),_('Selected duration is for %s days.So you have to take leave more than %s or equal to duration.')%(round(math.floor(diff_day))+1,vals['number_of_days_temp']))
						else:
							raise osv.except_osv(_('Warning!'),_('Please verify your leave number of days with duration which you have enter above.'))\

				##### Check Total leave available + Advance Leave
				if 'number_of_days_temp' in vals.keys(): 
					if 'total_available_leave' in vals.keys() and 'extra_leave_applied' in vals.keys():
						### Adding Extra leave
						if vals['is_leave_more'] == True:
							vals.update({'sub_extra_leave_applied':vals.get('extra_leave_applied')})
							vals['number_of_days_temp'] = vals['number_of_days_temp'] + vals.get('extra_leave_applied')
							if 'actual_num_temp_day' in vals:
								vals['actual_num_temp_day'] = vals['actual_num_temp_day'] + vals.get('extra_leave_applied')

						if vals['number_of_days_temp'] > vals['total_available_leave']:
							raise Warning(_("You don't have enough leaves to apply" ))
			 			if vals.get('advanced_leave') == 'yes':
							total_available = vals['total_available_leave'] + vals.get('advanced_leave_unit')
							if vals['number_of_days_temp'] > total_available:
								raise Warning(_("You don't have enough leaves to apply" ))
					elif 'total_available_leave' in vals.keys() and 'extra_leave_applied' not in vals.keys():
						### Adding Extra leave
						if vals['is_leave_more'] == True:
							vals.update({'sub_extra_leave_applied':write_leave_obj.extra_leave_applied})
							vals['number_of_days_temp'] = vals['number_of_days_temp'] + write_leave_obj.extra_leave_applied
							if 'actual_num_temp_day' in vals:
								vals['actual_num_temp_day'] = vals['actual_num_temp_day'] + write_leave_obj.extra_leave_applied
						if vals['number_of_days_temp'] > vals['total_available_leave']:
							raise Warning(_("You don't have enough leaves to apply" ))
			 			if vals.get('advanced_leave') == 'yes':
							total_available = vals['total_available_leave'] + vals.get('advanced_leave_unit')
							if vals['number_of_days_temp'] > total_available:
								raise Warning(_("You don't have enough leaves to apply" ))
					elif 'total_available_leave' not in vals.keys() and 'extra_leave_applied' in vals.keys():
						### Adding Extra leave
						if vals['is_leave_more'] == True:
							vals.update({'sub_extra_leave_applied':vals.get('extra_leave_applied')})
							vals['number_of_days_temp'] = vals['number_of_days_temp'] + vals.get('extra_leave_applied')
							if 'actual_num_temp_day' in vals:
								vals['actual_num_temp_day'] = vals['actual_num_temp_day'] + vals.get('extra_leave_applied')
						if vals['number_of_days_temp'] > write_leave_obj.total_available_leave:
							raise Warning(_("You don't have enough leaves to apply" ))
			 			if vals.get('advanced_leave') == 'yes':
							total_available = write_leave_obj.total_available_leave + vals.get('advanced_leave_unit')
							if vals['number_of_days_temp'] > total_available:
								raise Warning(_("You don't have enough leaves to apply" ))

					else:
						### Adding Extra leave
			 			if vals.get('advanced_leave') == 'yes':
							total_available = write_leave_obj.total_available_leave + vals.get('advanced_leave_unit')
							if vals['number_of_days_temp'] > total_available:
								raise Warning(_("You don't have enough leaves to apply" ))
						else:
							vals.update({'sub_extra_leave_applied':write_leave_obj.extra_leave_applied})
							vals['number_of_days_temp'] = vals['number_of_days_temp'] + write_leave_obj.extra_leave_applied
							if 'actual_num_temp_day' in vals:
								vals['actual_num_temp_day'] = vals['actual_num_temp_day'] + write_leave_obj.extra_leave_applied
							# if vals['number_of_days_temp'] > write_leave_obj.total_available_leave:
							# 	raise Warning(_("You don't have enough leaves to apply" ))

					####leave Applied validation
					if 'actual_num_temp_day' in vals:
						if vals['number_of_days_temp'] != vals['actual_num_temp_day']:
							vals['number_of_days_temp']= vals['actual_num_temp_day']
					else:
						if vals['number_of_days_temp'] != write_leave_obj.actual_num_temp_day:
							vals['number_of_days_temp']=  write_leave_obj.actual_num_temp_day

				###########Check Limit Defined in the not legal Leaves
				if "holiday_status_id" in vals:
					vals.update({'sub_total_available_leave':vals.get('total_available_leave')})
					if applied_leave_type.limit == True and applied_leave_type.is_unpaid==False:
						if 'number_of_days_temp' in vals.keys():
							if vals['number_of_days_temp'] > applied_leave_type.leave_limit:
								raise Warning(_("You are only allowed to take more than %s leaves" )%applied_leave_type.leave_limit)
						else:
							if leave_applied_temp > applied_leave_type.leave_limit:
								raise Warning(_("You are only allowed to take more than %s leaves" )%applied_leave_type.leave_limit)
					elif 'total_available_leave' in vals.keys() and 'number_of_days_temp' in vals.keys() :
						if vals['number_of_days_temp'] > vals['total_available_leave']:
							raise Warning(_("You don't have enough leaves to apply" ))
					elif 'total_available_leave' in vals.keys() and 'number_of_days_temp' not in vals.keys() :
						if write_leave_obj.number_of_days_temp > vals['total_available_leave']:
							raise Warning(_("You don't have enough leaves to apply" ))

				###Check Sandwich
				if 'is_sandwich' in vals and vals['is_sandwich']==True:
					vals['number_of_days_temp']=vals['number_of_days_temp']+vals.get('sandwich_days')
					if 'actual_num_temp_day' in vals:
						vals['actual_num_temp_day']=vals['actual_num_temp_day']+vals.get('sandwich_days')
				
			###########Validation for allocation request
			if write_leave_obj.type == 'add':
				if 'number_of_days_temp' in vals:
					if 'carry_forward' in vals and 'allocated_number' in vals:
						if vals['number_of_days_temp'] != vals['carry_forward'] + vals['allocated_number']:
							raise Warning(_("Total must be equal to sum of carry forward and current allocated" ))
					elif 'carry_forward' in vals:
						if vals['number_of_days_temp'] != vals['carry_forward'] + write_leave_obj.allocated_number:
							raise Warning(_("Total must be equal to sum of carry forward and current allocated" ))
					elif 'allocated_number' in vals:
						if vals['number_of_days_temp'] != write_leave_obj.carry_forward + vals['allocated_number']:
							raise Warning(_("Total must be equal to sum of carry forward and current allocated" ))
					else:
						if vals['number_of_days_temp'] != write_leave_obj.carry_forward + write_leave_obj.allocated_number:
							raise Warning(_("Total must be equal to sum of carry forward and current allocated" ))
##################Getting Value of State To Show In calender view ##########

			if 'state' in vals:
				state_dictionary = {'draft': 'In Draft','cancel': 'Cancelled','cancel_approval':'Waiting Cancel Approval','confirm': 'First Approval','refuse': 'Refused', 'validate1': 'Second Approval', 'validate':'Approved'}
				vals.update({'state_value':state_dictionary[vals['state']]})

		#################					
		#if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel','validate','validate1','cancel_approval']:
		#	raise osv.except_osv(_('Warning!'), _('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % vals.get('state'))
		return super(hr_holidays, self).write(cr, uid, ids, vals, context=context)

	def holidays_first_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		hr_records = self.browse(cr,uid,ids,context=None)
		for lines in hr_records:
			if lines.type == 'remove':
				if manager == lines[0].employee_id.parent_id.id:
					if lines.reasons_comment == False:
						raise osv.except_osv(_('Warning!'),_('Please Provide Reason in order to Approve this request in below form Reason box.\n Use Edit Button to record reasons.'))
					else:
						self.reasons_notificate(cr, uid, ids, context=context)
						self.write(cr,uid,ids,{'reasons_comment':False})

					self.holidays_first_validate_notificate(cr, uid, ids, context=context)
					return self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('First validation is only done by Manager of this user'))
			#if line.type == 'remove':
			#	if manager == lines[0].employee_id.parent_id.id or self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager'):
			#		self.holidays_first_validate_notificate(cr, uid, ids, context=context)
			#		return self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
			#	else:
			#		raise osv.except_osv(_('Warning!'),_('First validation is only done by Manager of this user'))

			if lines.type == 'add':
				if self.pool['res.users'].has_group(cr, uid, 'account.group_account_manager'):
					self.holidays_first_validate_notificate(cr, uid, ids, context=context)
					return self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('Only Account Manager have a access to approve this allocation request.'))


	def holidays_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		#self.write(cr, uid, ids, {'state':'validate'})
		data_holiday = self.browse(cr, uid, ids)

		for record in data_holiday:
			if record.type == 'remove':
				if record.double_validation:
					if self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager') or self.pool['res.users'].has_group(cr, uid, 'base.group_hr_user'):
						if record.reasons_comment == False:
							raise osv.except_osv(_('Warning!'),_('Please Provide Reason in order to Approve this request in below reason box.\n Use Edit Button to record reasons.'))
						else:
							self.reasons_notificate(cr, uid, ids, context=context)
							self.write(cr,uid,ids,{'reasons_comment':False})
						
						self.write(cr, uid, ids, {'state':'validate'})
						self.write(cr, uid, [record.id], {'manager_id2': manager})
					else:
						# self.write(cr, uid, [record.id], {'manager_id': manager})
						raise osv.except_osv(_('Warning!'),_('Only Access right with HR Manager/Officer will able to do Second Approval'))
			if record.type == 'add':
				if self.pool['res.users'].has_group(cr, uid, 'account.group_account_manager'):
					self.write(cr, uid, ids, {'state':'validate'})
					self.write(cr, uid, [record.id], {'manager_id2': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('Only Account Manager have a access to approve this allocation request.'))

			if record.holiday_type == 'employee' and record.type == 'remove':
				meeting_obj = self.pool.get('calendar.event')
				meeting_vals = {
					'name': record.name or _('Leave Request'),
					'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
					'duration': record.number_of_days_temp * 8,
					'description': record.notes,
					'user_id': record.user_id.id,
					'start': record.date_from,
					'stop': record.date_to,
					'allday': False,
					'state': 'open',            # to block that meeting date in the calendar
					'class': 'confidential'
				} 
				#Add the partner_id (if exist) as an attendee
				if record.user_id and record.user_id.partner_id:
					meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]
				ctx_no_email = dict(context or {}, no_email=True)
				meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
				self._create_resource_leave(cr, uid, [record], context=context)
				self.write(cr, uid, ids, {'meeting_id': meeting_id})
			elif record.holiday_type == 'category':
				emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
				leave_ids = []
				for emp in obj_emp.browse(cr, uid, emp_ids):
					vals = {
						'name': record.name,
						'type': record.type,
						'holiday_type': 'employee',
						'holiday_status_id': record.holiday_status_id.id,
						'date_from': record.date_from,
						'date_to': record.date_to,
						'notes': record.notes,
						'number_of_days_temp': record.number_of_days_temp,
						'parent_id': record.id,
						'employee_id': emp.id
					}

					leave_ids.append(self.create(cr, uid, vals, context=None))
				for leave_id in leave_ids:
					# TODO is it necessary to interleave the calls?
					for sig in ('confirm', 'validate', 'second_validate'):
						self.signal_workflow(cr, uid, [leave_id], sig)
		return True

	def holidays_refuse(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		for holiday in self.browse(cr, uid, ids, context=context):

			if holiday.type == 'remove':
				if holiday.state == 'validate1' and holiday[0].employee_id.parent_id.id == manager:
					raise osv.except_osv(_('Warning!'),_('You are not allowed to refuse your subordinate Leave in Second Approval State.'))

				if holiday.reasons_comment == False:
					raise osv.except_osv(_('Warning!'),_('Please Provide Reason in order to refuse this request in below reason box.\n Use Edit Button to record reasons.'))
				else:
					self.reasons_notificate(cr, uid, ids, context=context)
					self.write(cr,uid,ids,{'reasons_comment':False})

			if holiday.state == 'validate1':
				if manager != holiday[0].employee_id.id or self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager'):
					self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('You are not allowed to refuse your own leave request.'))
			else:
				self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id2': manager})
		self.holidays_cancel(cr, uid, ids, context=context)
		return True

	def reasons_notificate(self, cr, uid, ids, context=None):
		for obj in self.browse(cr, uid, ids, context=context):
			self.message_post(cr, uid, [obj.id],_('%s \n\n Employee Name: %s and Applied For %s to %s.') % (context['reason'],obj.employee_id.name,obj.date_from,obj.date_to), subtype='mt_comment',context=context)

	def onchange_holiday_status_id(self, cr, uid, ids,date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp,context=None):
		result = {'value': {}}
		result=self.validate_leave_policy(cr, uid, ids,date_to, date_from,holiday_status_id,employee_id,advanced_leave,number_of_days_temp, context=None)
		return result
		
	def onchange_advance_leave(self, cr, uid, ids,number_of_days_temp,holiday_status_id,advanced_leave,advanced_leave_unit,employee_id):
		result = {'value': {}}
		now = datetime.datetime.now()
		month = now.strftime('%B')
		start_date = (datetime.datetime.now()).replace(day=1,month=1).strftime("%Y-%m-%d")
		end_date = (datetime.datetime.now()).replace(day=31,month=12).strftime("%Y-%m-%d")
		advance_leave_so_far=0.0
		leave_type_obj=self.pool.get('hr.holidays.status')
		company_id_leave_policy=self.get_company_id_apply_leave_policy(cr,uid,ids,context=None)
		if company_id_leave_policy:
			if holiday_status_id:
				leave_type_obj_browse=leave_type_obj.browse(cr,uid,holiday_status_id)
				if leave_type_obj_browse.is_el == True:
					if advanced_leave == 'yes':
						if month not in ['October','November','December']:
						############Advance Leave taken
							advance_leave_ids = self.search(cr, uid, [('employee_id', '=', employee_id),
                                                                ('state', 'in',['validate','validate1']),
                                                                ('type','=','remove'),
                                                                ('advanced_leave','=','yes'),
                                                               	('date_from','>=',start_date),
                                                               	('date_to','<=', end_date)])
							for advance_leave_browse in self.browse(cr, uid,advance_leave_ids ):
								advance_leave_so_far += advance_leave_browse.advanced_leave_unit

							left_advance_leave = 4.0 - advance_leave_so_far

							if advanced_leave_unit > left_advance_leave:
								raise Warning(_('Only %s days advance leave left for you.')%(left_advance_leave))

							if advanced_leave_unit <= 4.0:
								result['value']['advanced_leave_unit']=advanced_leave_unit
								result['value']['number_of_days_temp']= number_of_days_temp+advanced_leave_unit
							else:
								raise Warning(_('You are not allowed to take more than 4 days advance leave'))
						else:
							raise Warning(_('Advance Leave is allowed till September'))
			return result

	def onchange_number_of_days_temp(self, cr, uid, ids,number_of_days_temp, date_to, date_from,holiday_status_id,context=None):
		result = {'value': {}}
		holiday_request_id = self.browse(cr,uid,ids)
		leave_days=self.pool.get('hr.holidays.status').get_days(cr, uid, [holiday_status_id], holiday_request_id.employee_id.id)[holiday_status_id]
		if holiday_request_id.type == 'remove':
			if holiday_request_id.holiday_status_id.limit == False and holiday_request_id.id != False:
				if  number_of_days_temp > leave_days['remaining_leaves']:
					raise osv.except_osv(_('Warning!'),_('You are not allowed to take %s leave. Please check your remaining leave.')%(number_of_days_temp))
				else:
					result['value']['number_of_days_temp'] = number_of_days_temp
					return result
		return True

	############## Cron Jobs #############
	def fetching_employee_manager(self, cr, uid,automatic=False, context=None):
		search_hr_records = self.search(cr,uid,[('manager_id', '=', False),('type','=','remove'),('holiday_type','=','employee'),('state','=','confirm')], context=context)
		employee_obj=self.pool.get('hr.employee')
		for employee_holiday in self.browse(cr, uid, search_hr_records, context=context):
				employees_record = employee_obj.browse(cr,uid,[employee_holiday.employee_id.id])
				if employees_record.active == True:
					self.write(cr,uid,[employee_holiday.id],{'manager_id': employees_record.parent_id.id}, context=context)
		return True

	def fetching_leave_state_value(self, cr, uid,automatic=False, context=None):
		leave_state_records = self.search(cr,uid,[('type','=','remove')], context=context)
		for state_record_list in self.browse(cr, uid,leave_state_records, context=context):
			state_dictionary = {'draft': 'In Draft','cancel': 'Cancelled','cancel_approval':'Waiting Cancel Approval','confirm': 'First Approval','refuse': 'Refused', 'validate1': 'Second Approval', 'validate':'Approved'}
			self.write(cr,uid,[state_record_list.id],{'state_value': state_dictionary[state_record_list.state]}, context=context)

		return True

	
	def leave_cancel(self, cr, uid, ids, context=None):
		for holiday in self.browse(cr, uid, ids, context=context):
			if holiday.type == 'remove':
				if holiday.user_id.id != uid and not self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager'):
					raise osv.except_osv(_('Warning!'),_('You are not allowed to cancel your subordinate leave request.'))

				if holiday.reasons_comment == False:
					raise osv.except_osv(_('Warning!'),_('Please Provide Reason in order to cancel this request in below reason box.\n Use Edit Button to record reasons.'))	
				else:
					self.reasons_notificate(cr, uid, ids, context=context)
					self.write(cr,uid,ids,{'reasons_comment':False,'state':'cancel_approval'})
		return True

	def leave_cancel_approve(self, cr, uid, ids, context=None):
		holiday_record = self.browse(cr, uid, ids, context=context)
		if holiday_record.user_id.id == uid :
			raise osv.except_osv(_('Warning!'),_('You are not allowed to approve  your own cancel leave request.'))
		else:
			self.write(cr,uid,ids,{'state':'cancel'})
			#self.holidays_cancel(cr, uid, ids, context=context)
		return True

	def reset_to_draft(self, cr, uid, ids, context=None):
		return self.write(cr,uid,ids,{'state':'confirm','manager_id': False,
            'manager_id2': False,})

	##### Exception log for Leave
	def run_leave_log_by_employee(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
		employee_record_obj = self.pool.get('hr.employee')
		company_obj = self.pool.get('res.company')
		date_today = datetime.datetime.today()
		start_year = (datetime.datetime.now()).replace(day=1,month=1).strftime("%Y-%m-%d")
		end_year = (datetime.datetime.now()).replace(day=31,month=12).strftime("%Y-%m-%d")
		add_row = ''
		body_part_company = ''
		state_dictionary = {'draft': 'In Draft','cancel': 'Cancelled','cancel_approval':'Waiting Cancel Approval','confirm': 'First Approval','refuse': 'Refused', 'validate1': 'Second Approval', 'validate':'Approved'}
		for company_id in company_obj.search(cr,uid,[('parent_id','=',False)], context=context):
			company_name = company_obj.browse(cr, uid, company_id).name
			employee_record_search =  employee_record_obj.search(cr,uid,[('active','=',True),('user_id','!=',1),('company_id','=',company_id)])
			for employee_list in employee_record_obj.browse(cr,uid,employee_record_search):
				if employee_list.user_id :
					leave_record_search = self.search(cr,uid,[('user_id','=',employee_list.user_id.id),('state','!=','validate'),('leave_allocate_year_start','>=',start_year),('leave_allocate_year_end','<=', end_year),('type','=','remove')])
					if leave_record_search != []:
						for leave_applied in self.browse(cr,uid,leave_record_search):
							write_date_format = datetime.datetime.strptime(leave_applied.write_date,"%Y-%m-%d %H:%M:%S")
							diff_leave = (date_today-write_date_format).days
			 				add_row += '''<tr bgcolor="#d7e9fa"><td> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> </tr>''' %(employee_list.name,leave_applied.create_date,employee_list.parent_id.name,state_dictionary[leave_applied.state],diff_leave)
			##########Create Body part for Different Company ############
			body_part_company += ''' <div><h4 style="background: rgb(51,255,153);"> %s Company Leave Log</h4>
										<table>
											<thead>
												<tr bgcolor="#f2f3f2">
													<th style="width:24%%">Employee Name </th>
													<th style="border-right: 1px solid #ccc;"> Applied on </th>
													<th style="border-right: 1px solid #ccc;"> Reporting Manager </th>
													<th style="border-right: 1px solid #ccc;"> Leave Status </th>
													<th style="border-right: 1px solid #ccc;"> Pending Duration (in days)</th>
												</tr>
											</thead>
											<tbody>
												%s
											</tbody>
										</table>
									</div> '''%(company_name,add_row)
			add_row = ''
			#######################################################
		body_html = '''<html>
							<head></head>
							<body>
								<p> Hi,</p>
								<p> Below are the Leave exception Log send by Intranet</p>
								%s
							</body>
						</html>
					''' %(body_part_company)
		sub = 'Employee Leave Exceptional Log From Intranet'
		irconfig_obj = self.pool['ir.config_parameter']
		email_from = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.analytic.timesheet.email_from')
		email_to = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.leave.exception.email_to')
		vals = {'state': 'outgoing',
				'subject': sub,
				'body_html': '<pre>%s</pre>' % body_html,
				'email_to': email_to,
				'email_from': email_from,
				}
		self.pool.get('mail.mail').create(cr, uid, vals, context=context)
		return True


class hr_employee(osv.osv):
	_inherit="hr.employee"

	_columns={
		'date_of_joining':fields.date("Date of Joining",help="Enter Date of Joining of this employee"),
	}


class leave_mechanism(osv.osv):
	_name='leave.mechanism'

	def _get_default_company(self, cr, uid, context=None):
		company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
		if not company_id:
			raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
		return company_id

	_columns={
		'name':fields.char("Leave Mechanism",required=True),
		'mechanism_line':fields.one2many('leave.mechanism.line', 'mechanism_id', 'Mechanism Details',copy=True),
		'active':fields.boolean("Active"),
		'company_ids':fields.many2many('res.company','leave_mechanism_rel', 'leave_mechanism_id', 'company_id', string='Companies'),

	}

	_defaults = {
		'active':True,
		'company_id':_get_default_company,
	}

class leave_mechanism_line(osv.osv):
	_name='leave.mechanism.line'

	_columns={
		'year_value':fields.integer("Year Integer value"),
		'name':fields.selection([('January','January'),
			('February','February'),('March','March'),
			('April','April'),('May','May'),('June','June'),('July','July'),
			('August','August'),('September','September'),('October','October'),
			('November','November'),('December','December')],string="Leave Mechanism Month", required=True),
		'subjected_cl':fields.integer("Subjected CL's"),
		'subjected_el':fields.integer("Subjected EL's"),
		'mechanism_id':fields.many2one('leave.mechanism', 'Leave Mechanism', required=True, ondelete='cascade', select=True ),
	}