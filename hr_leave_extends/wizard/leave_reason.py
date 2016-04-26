from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_holidays_leave_reason(osv.osv_memory):
	_name = 'hr.holidays.leave.reason'
	_description = 'HR Leaves Reasons for Approval'

	def _get_leave_state(self,cr,uid,context=None):
		leave_object = self.pool.get('hr.holidays')
		return context['event_type']

	_columns = {
		'state': fields.selection([('confirm', 'To Approve'),('validate1', 'Second Approval'),('cancel','Cancel'),('refuse', 'Refused')], 'Leave Type', required=True),
		'leave_reason':fields.text("Provide Reason",required=True),
	}

	_defaults = {
		'state':_get_leave_state,
	}

	def holidays_first_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		leave_object = self.pool.get('hr.holidays')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		reason_text=self.browse(cr,uid,ids).leave_reason
		context.update({'reason':reason_text})
		manager = ids2 and ids2[0] or False
		hr_records = leave_object.browse(cr,uid,context['active_id'])
		for lines in hr_records:
			if lines.type == 'remove':
				if manager == lines[0].employee_id.parent_id.id:
					leave_object.reasons_notificate(cr, uid, hr_records.id, context=context)
					leave_object.holidays_first_validate_notificate(cr, uid, hr_records.id, context=context)
					return leave_object.write(cr, uid, [hr_records.id], {'state':'validate1', 'manager_id': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('First validation is only done by Manager of this user'))
			if lines.type == 'add':
				if self.pool['res.users'].has_group(cr, uid, 'account.group_account_manager'):
					leave_object.holidays_first_validate_notificate(cr, uid, hr_records.id, context=context)
					return leave_object.write(cr, uid, [hr_records.id], {'state':'validate1', 'manager_id': manager})
				else:
					raise osv.except_osv(_('Warning!'),_('Only Account Manager have a access to approve this allocation request.'))

	def holidays_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		leave_object = self.pool.get('hr.holidays')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		data_holiday = leave_object.browse(cr, uid, context['active_id'])
		reason_text=self.browse(cr,uid,ids).leave_reason
		context.update({'reason':reason_text})
		for record in data_holiday:
			if record.type == 'remove':
				if record.double_validation:
					if self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager') or self.pool['res.users'].has_group(cr, uid, 'base.group_hr_user'):
						leave_object.reasons_notificate(cr, uid, record.id, context=context)
						leave_object.write(cr, uid, [record.id], {'manager_id2': manager,'state':'validate'})
					else:
						raise osv.except_osv(_('Warning!'),_('Only Access right with HR Manager/Officer will able to do Second Approval'))

			if record.type == 'add':
				if self.pool['res.users'].has_group(cr, uid, 'account.group_account_manager'):
					leave_object.write(cr, uid, [record.id], {'manager_id2': manager,'state':'validate'})
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
				leave_object._create_resource_leave(cr, uid, [record], context=context)
				leave_object.write(cr, uid, ids, {'meeting_id': meeting_id})
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
					leave_ids.append(leave_object.create(cr, uid, vals, context=None))
				for leave_id in leave_ids:
					# TODO is it necessary to interleave the calls?
					for sig in ('confirm', 'validate', 'second_validate'):
						leave_object.signal_workflow(cr, uid, [leave_id], sig)
		return True

	def holidays_refuse_reason(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		leave_object = self.pool.get('hr.holidays')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		reason_text=self.browse(cr,uid,ids).leave_reason
		context.update({'reason':reason_text})
		manager = ids2 and ids2[0] or False
		for holiday in leave_object.browse(cr, uid, context['active_id']):
			if holiday.type == 'remove':
				if holiday.state == 'validate1' and holiday[0].employee_id.parent_id.id == manager:
					raise osv.except_osv(_('Warning!'),_('You are not allowed to refuse your subordinate Leave in Second Approval State.'))
				if holiday.state == 'validate1':
					if manager != holiday[0].employee_id.id or self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager'):
						leave_object.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id': manager})
					else:
						raise osv.except_osv(_('Warning!'),_('You are not allowed to refuse your own leave request.'))
				else:
					leave_object.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id2': manager})
				leave_object.reasons_notificate(cr, uid, holiday.id, context=context)
			leave_object.holidays_cancel(cr, uid, [holiday.id], context=context)
		return True

	def leave_cancel_reason(self, cr, uid, ids, context=None):
		leave_object = self.pool.get('hr.holidays')
		reason_text=self.browse(cr,uid,ids).leave_reason
		context.update({'reason':reason_text})
		for holiday in leave_object.browse(cr, uid, context['active_id']):
			if holiday.type == 'remove':
				if holiday.user_id.id != uid and not self.pool['res.users'].has_group(cr, uid, 'base.group_hr_manager'):
					raise osv.except_osv(_('Warning!'),_('You are not allowed to cancel your subordinate leave request.'))
				leave_object.reasons_notificate(cr, uid, holiday.id, context=context)
				leave_object.write(cr,uid,[holiday.id],{'state':'cancel_approval'})
		return True