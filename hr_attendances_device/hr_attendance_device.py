import time
from datetime import *
from openerp import SUPERUSER_ID
from openerp.osv import fields,osv
from openerp.tools.translate import _
import xmlrpclib
from ctypes import *


class hr_attendance_device(osv.osv):
	_name = 'hr.attendance.device'
	_description = 'Attendance Device Configuration'
	_columns = {
		'name':fields.char("Device name",required=True,help="Enter a Name of the device"),
		'device_ip':fields.char("Host IP Address",required=True,help="Enter IP Address of the Device"),
		'device_number':fields.integer("Device Number",required=True),
		'device_port':fields.integer("Port",required=True,help="Enter device port number.Default is 4370"),
		'timezone':fields.integer("Timezone"),
		'active': fields.boolean('Active'),
	}
	_defaults = {
		'active': 1,
		'device_port':4370,
		'timezone': 2,
	}
	_order = 'name'

	def check_device_connection(self, cr, uid, ids, context=None):
		record_id = self.browse(cr,uid,ids,context=context)[0]
		params = "protcol=TCP,ipaddress=" + str(record_id.device_ip) + ",port=" + str(record_id.device_port) + ",timeout=5000,passwd="
		connect_value = False
		irconfig_obj = self.pool['ir.config_parameter']
		window_server = irconfig_obj.get_param(cr, SUPERUSER_ID, 'window.server.host_url')
		try:
			server = xmlrpclib.ServerProxy(window_server)
			connect_value = server.connect(str(record_id.device_ip),str(record_id.device_port))
		except:
			print "We faced some error in Connection. Either your Server is Down or internet Connection is Slow"
		if connect_value == 0:
			raise osv.except_osv(_('Information'),_('Connection UnSuccessful'))
		else :
			raise osv.except_osv(_('Information'),_('Connection Successful'))
			server.disconnect(connect_value)
		return True

class hr_employee (osv.osv):
	_inherit = "hr.employee"
	_columns = {
		'pin_number': fields.integer("Device Personal Number",required=True,help="Enter the user Personal Number/Pin Number"),
		'card_number':fields.integer("Card Number",required=True,help="Card Number of a User"),
	}

	_defaults = {
	 	'pin_number': 0,
	 	'card_number': 0,
	}

class hr_attendance(osv.osv):
	_inherit = "hr.attendance"

	_columns = {
		'pin_number':fields.integer("Device Personal Number",required=True,help="Enter the User Peronal Number/Pin Number"),
		'card_number':fields.integer("Card Number",required=True,help="Card Number of a Use0r"),
		'verified_mode':fields.selection([('1', 'Only Finger'), ('3', 'Only Password'), ('4','Only Card'),('11','Card and Password'),('200','Others')], 'Verified Mode', required=True),

	}
	_defaults = {
	 	'verified_mode': '4',
	}

class zksoftware_downloader(osv.osv_memory):
	_name = "zksoftware.downloader"
	_description = "ZkSoftware Downloader"
	_columns = {
	 		'all_employee' : fields.boolean("All Employee"),
	 		'filter_date': fields.boolean("Filter By date"),
	 		'date_from' :fields.datetime ("Date From"),
	 		'date_to':fields.datetime("Date To"),
	 		'employee_id':fields.many2many('hr.employee', string='Employee'),
	 		'device_configuration':fields.many2many('hr.attendance.device', string='Choose Devices'),

	
 	}

 	def _get_all_devices(self, cr, uid, context=None):
 		return self.pool.get('hr.attendance.device').search(cr, uid ,[('active','=',True)])

 	_defaults = {
 		'device_configuration':_get_all_devices,
 		'all_employee':True,
 	}

 	def timesecond_to_datetime(self,value):
		date_format = ''
		second = value % 60
		value /= 60
		minute = value % 60
		value /=60
		hour = value % 24
		value /=24
		date = value % 31 +1
		value /=31
		month = value % 12 +1
		value /=12
		year = value + 2000
		date_output = date_format + str(year) + '-' + str(month) + '-' + str(date) + ' ' + str(hour) + ':' + str(minute) + ':' + str(second)
		return date_output

	def fetch_device_record(self, cr, uid, pin_number,card_number,device_ip,device_port):
		table = 'transaction'
		fieldname = "*"																			
		filter_device = "Pin=" + str(pin_number) + ",Cardno=" + str(card_number)
		options = ""
		query_buf = 4*1024*1024
		get_log = ''
		irconfig_obj = self.pool['ir.config_parameter']
		window_server = irconfig_obj.get_param(cr, SUPERUSER_ID, 'window.server.host_url')
		
 		try:
			server = xmlrpclib.ServerProxy(window_server)
			connect_value = server.connect(str(device_ip),str(device_port))
			if connect_value != 0:
				get_log = server.get_alldata(connect_value,query_buf,query_buf,table,fieldname,filter_device,options)
			disconnect=server.disconnect(connect_value)
			if connect_value <= 0 or get_log ==  True:
				body_html = '''<html><head></head><body> <p>The cron Job script is not running properly in %s which is responsible for fetching attendance data into Intranet</p><p> Please take care</p></body></html>''' %(window_server)
				sub = 'Attendance System script not working'
				email_to = irconfig_obj.get_param(cr, SUPERUSER_ID, 'window.server.unsuccessful_connection.email_id')
				email_from = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.analytic.timesheet.email_from')
				email_vals = {'state': 'outgoing',
            					'subject': sub,
            					'body_html': '<pre>%s</pre>' % body_html,
            					'email_to': email_to,
            					'email_from': email_from,
           					}
				self.pool['mail.mail'].create(cr, uid, email_vals)
		except:
			print "We faced some error in Connection. Either your Server is Down or internet Connection is Slow"
			raise osv.except_osv(_('Information'),_('We faced some error in Connection.\n Either your Server is Down or internet Connection is Slow'))
		return get_log

	


 	def download_device_record(self, cr, uid, ids, context=None):
 		if context is None:
 			context = {}
 		hr_employee_obj = self.pool.get('hr.employee')
 		zk_devices_obj = self.pool.get('hr.attendance.device')
 		hr_attendance_obj = self.pool.get ('hr.attendance')
 		today = datetime.today()
 		new_today = (today + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
 		new_today_utc = datetime.strptime(new_today, '%Y-%m-%d %H:%M:%S')
 		form_details = self.read(cr, uid, ids, ['date_from',  'date_to',  'device_configuration', 'employee_id', 'filter_date', 'all_employee'], context=context)[0]
 		if form_details['device_configuration'] != [] and len(form_details['device_configuration']) == 1:
 			zk_devices_browse = zk_devices_obj.browse(cr,uid,form_details['device_configuration'])
 			if form_details['all_employee'] == True and form_details['filter_date'] == False:
 				hr_employee_search = hr_employee_obj.search(cr,uid,[('active','=',True),('pin_number','!=',0),('card_number','!=',0)])
 				if hr_employee_search != []:
 					for employee in hr_employee_obj.browse(cr,uid,hr_employee_search):
 						get_log = self.fetch_device_record(cr, uid, employee.pin_number, employee.card_number, zk_devices_browse.device_ip, zk_devices_browse.device_port)
 						if get_log == True:
 							break
 						hr_attendance_search = hr_attendance_obj.search(cr,uid,[('employee_id', '=',employee.id)])
 						if hr_attendance_search != []:
 							hr_attendance_browse = hr_attendance_obj.browse(cr,uid,hr_attendance_search[0])
 							last_update = datetime.strptime(hr_attendance_browse.name, '%Y-%m-%d %H:%M:%S')
 							last_update_utc = last_update + timedelta(hours=5,minutes=30) 
 							if new_today_utc > last_update_utc:
 								all_log = get_log.split("\\r\\n")
								for logs in range(1,len(all_log)-1) :
									#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									current_next_date_check = ''
									if logs >= 2:
										log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
										current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
									log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
									current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
									current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
									#if current_date != current_next_date_check or current_next_date_check == '':
									#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									if current_date > last_update_utc:
										if int(all_log[logs].split(',')[5]) == 0 :
											vals = {'employee_id':employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
										else:
											vals = {'employee_id':employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
										#hr_attendance_obj.create(cr,uid,vals)
										self.creating_single_attendance_record(cr, uid, vals)
						else:
							all_log = get_log.split("\\r\\n")
							for logs in range(1,len(all_log)-1) :
								#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
								current_next_date_check = ''
								if logs >= 2:
									log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
									current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
								current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
								current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
								#if current_date != current_next_date_check or current_next_date_check == '':
								#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								if int(all_log[logs].split(',')[5]) == 0 :
									vals = {'employee_id':employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
								else:
									vals = {'employee_id':employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
								#hr_attendance_obj.create(cr,uid,vals)
								self.creating_single_attendance_record(cr, uid, vals)

			elif form_details['all_employee'] == False and form_details['filter_date'] == False:
				for selected_employee in hr_employee_obj.browse(cr,uid,form_details['employee_id']):
					if selected_employee.pin_number != 0 and selected_employee.card_number != 0:
						record_log = self.fetch_device_record(cr, uid, selected_employee.pin_number,selected_employee.card_number,zk_devices_browse.device_ip,zk_devices_browse.device_port)
						if record_log == True:
 							break
						hr_attendance_search = hr_attendance_obj.search(cr,uid,[('employee_id', '=',selected_employee.id)])
						if hr_attendance_search != []:
							hr_attendance_browse = hr_attendance_obj.browse(cr,uid,hr_attendance_search[0])
							last_update = datetime.strptime(hr_attendance_browse.name, '%Y-%m-%d %H:%M:%S')
							last_update_utc = last_update + timedelta(hours=5,minutes=30)
							if new_today_utc > last_update_utc:
 								all_log = record_log.split("\\r\\n")
								for logs in range(1,len(all_log)-1) :
									#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
									current_next_date_check = ''
									if logs >= 2:
										log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
										current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
									current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
									current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
									#if current_next_date_check != current_date or current_next_date_check == '':
									#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									if current_date > last_update_utc:
										if int(all_log[logs].split(',')[5]) == 0 :
											vals = {'employee_id':selected_employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':selected_employee.pin_number,'card_number':selected_employee.card_number,'verified_mode':'4'}
										else:
											vals = {'employee_id':selected_employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':selected_employee.pin_number,'card_number':selected_employee.card_number,'verified_mode':'4'}
										#hr_attendance_obj.create(cr,uid,vals)
										self.creating_single_attendance_record(cr, uid, vals)
						else:
							all_log = record_log.split("\\r\\n")
							for logs in range(1,len(all_log)-1) :
								#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
								current_next_date_check = ''
								if logs >= 2:
									log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
									current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
								current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
								current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
								#if current_next_date_check != current_date or current_next_date_check == '':
								#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								if int(all_log[logs].split(',')[5]) == 0 :
									vals = {'employee_id':selected_employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':selected_employee.pin_number,'card_number':selected_employee.card_number,'verified_mode':'4'}
								else:
									vals = {'employee_id':selected_employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':selected_employee.pin_number,'card_number':selected_employee.card_number,'verified_mode':'4'}
								#hr_attendance_obj.create(cr,uid,vals)
								self.creating_single_attendance_record(cr, uid, vals)

			elif form_details['filter_date'] == True:
				date_from = datetime.strptime(form_details['date_from'].split()[0],'%Y-%m-%d') + timedelta()
				date_to = datetime.strptime(form_details['date_to'].split()[0],'%Y-%m-%d') + timedelta()
				hr_employee_search = hr_employee_obj.search(cr,uid,[('active','=',True),('pin_number','!=',0),('card_number','!=',0)])
				if hr_employee_search != []:
 					for employee in hr_employee_obj.browse(cr,uid,hr_employee_search):
 						get_log = self.fetch_device_record(cr, uid, employee.pin_number, employee.card_number, zk_devices_browse.device_ip, zk_devices_browse.device_port)
 						if get_log == True:
 							break
 						hr_attendance_search = hr_attendance_obj.search(cr,uid,[('employee_id', '=',employee.id),('name','>=',str(date_from)),('name','<=',str(date_to))])
 						if hr_attendance_search != []:
 							hr_attendance_browse = hr_attendance_obj.browse(cr,uid,hr_attendance_search[0])
 							last_update = datetime.strptime(hr_attendance_browse.name, '%Y-%m-%d %H:%M:%S')
 							last_update_utc = last_update + timedelta(hours=5,minutes=30) 
 							if date_to > last_update_utc:
 								all_log = get_log.split("\\r\\n")
								for logs in range(1,len(all_log)-1) :
									#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
									current_next_date_check = ''
									if logs >= 2:
										log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
										current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
									current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
									current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
									#if current_next_date_check != current_date or current_next_date_check == '':
									#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
									if current_date > last_update_utc and current_date < date_to:
										if int(all_log[logs].split(',')[5]) == 0 :
											vals = {'employee_id':employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
										else:
											vals = {'employee_id':employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
										#hr_attendance_obj.create(cr,uid,vals)
										self.creating_single_attendance_record(cr, uid, vals)
 						else:
 							all_log = get_log.split("\\r\\n")
							for logs in range(1,len(all_log)-1) :
								#if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
								current_next_date_check = ''
								if logs >= 2:
									log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
									current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
								current_date = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S')
								current_date_utc = current_date + timedelta(hours=-5,minutes=-30)
								#if current_next_date_check != current_date or current_next_date_check == '':
								#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								if current_date > date_from and current_date < date_to:
									if int(all_log[logs].split(',')[5]) == 0 :
										vals = {'employee_id':employee.id,'action':'sign_in','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
									else:
										vals = {'employee_id':employee.id,'action':'sign_out','name':str(current_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
									#hr_attendance_obj.create(cr,uid,vals)
									self.creating_single_attendance_record(cr, uid, vals)
		else:			
			raise osv.except_osv(_('Information'),_('Add Only One device In order to Fetch Attendance Record.'))


 		return True



 	def run_attendance_log_from_device(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
 		zk_devices_obj = self.pool.get('hr.attendance.device')
 		hr_employee_obj = self.pool.get('hr.employee')
 		hr_attendance_obj = self.pool.get ('hr.attendance')
 		zk_devices_search = zk_devices_obj.search(cr,uid,[('active','=','True')])
 		if len(zk_devices_search) == 1 :
 			zk_devices_browse = zk_devices_obj.browse(cr,uid,zk_devices_search)
 		else :
 			raise osv.except_osv(_('Warning'),_('There is no device which is active to fetch data or You configured more then two active device'))
 		today = datetime.today()
 		new_today = (today + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
 		new_today_utc = datetime.strptime(new_today, '%Y-%m-%d %H:%M:%S')
 		hr_employee_search = hr_employee_obj.search (cr,uid,[('active','=',True),('pin_number','!=',0),('card_number','!=',0)])
 		for employee in hr_employee_obj.browse(cr,uid,hr_employee_search):
 			get_log = self.fetch_device_record(cr, uid, employee.pin_number, employee.card_number, zk_devices_browse.device_ip, zk_devices_browse.device_port)
 			if get_log == True:
 				break
			if hr_employee_search != []:
				hr_attendance_search = hr_attendance_obj.search(cr,uid,[('employee_id','=',employee.id)])
				if hr_attendance_search != []:
					hr_attendance_browse = hr_attendance_obj.browse(cr,uid,hr_attendance_search[0])
					last_update = datetime.strptime(hr_attendance_browse.name, '%Y-%m-%d %H:%M:%S')
					last_update_utc = last_update + timedelta(hours=5,minutes=30)
					if new_today_utc > last_update_utc:
						if get_log != True:
							all_log = get_log.split("\\r\\n")
							for logs in range(1,len(all_log)-1) :
								log_date = self.timesecond_to_datetime(int(all_log[logs].split(',')[6]))
								current_next_date_check = ''
								if logs >= 2:
									log_date_next_check = self.timesecond_to_datetime(int(all_log[logs-1].split(',')[6]))
									current_next_date_check = datetime.strptime(log_date_next_check, '%Y-%m-%d %H:%M:%S')
								log_date_update = datetime.strptime(log_date, '%Y-%m-%d %H:%M:%S') 
								log_date_utc = log_date_update + timedelta(hours=-5,minutes=-30)
								#if current_next_date_check != log_date_update or current_next_date_check == '':
								#	if all_log[logs-1].split(',')[5] != all_log[logs].split(',')[5]:
								if log_date_update > last_update_utc:
									if int(all_log[logs].split(',')[5]) == 0 :
										vals = {'employee_id':employee.id,'action':'sign_in','name':str(log_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
									else:
										vals = {'employee_id':employee.id,'action':'sign_out','name':str(log_date_utc),'pin_number':employee.pin_number,'card_number':employee.card_number,'verified_mode':'4'}
									#hr_attendance_obj.create(cr,uid,vals)
									self.creating_single_attendance_record(cr, uid, vals)
									

		return True

	def creating_single_attendance_record(self, cr, uid, vals):
		hr_attendance_obj_create = self.pool.get ('hr.attendance')
		return hr_attendance_obj_create.create(cr, uid, vals)


class hr_attendance_record_report (osv.osv):
	_name = "hr_attendance.record.report"
	_description = "Attendance New Module"

	_columns = {
		'name': fields.date("Date",required=True),
		'employee_id': fields.many2one("hr.employee", "Employee Name", required=True),
		'sign_in': fields.datetime("Sign_In Time"),
		'sign_out': fields.datetime("Sign_out Time"),
		'total_duration':fields.float("Total Duration"),

	}

	_order = 'name desc'


	def run_attendance_record_report_data(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
		hr_employee_obj = self.pool.get('hr.employee')
 		hr_attendance_obj = self.pool.get ('hr.attendance')
 		hr_attendance_record_obj = self.pool.get ('hr_attendance.record.report')
 		hr_employee_search = hr_employee_obj.search (cr,uid,[('active','=',True),('pin_number','!=',0),('card_number','!=',0)])
 		for employee_list in hr_employee_obj.browse(cr,uid,hr_employee_search):
 			hr_attendance_search = hr_attendance_obj.search(cr,uid,[('employee_id','=',employee_list.id)], order='name ASC')
 			if hr_attendance_search != []:
 				first_attendance_record = hr_attendance_obj.browse(cr,uid,hr_attendance_search[0])
 				first_att_record_date = datetime.strptime(first_attendance_record.name, '%Y-%m-%d %H:%M:%S')
 				first_date = first_attendance_record.name
 				attendance_report_record_status = hr_attendance_record_obj.search(cr,uid,[('employee_id','=',employee_list.id)])
 				list_for_same_date = []
 				if attendance_report_record_status == []:
 					for employee_records in range(0,len(hr_attendance_search)):
 						employee_attendance_record = hr_attendance_obj.browse(cr,uid,hr_attendance_search[employee_records])
 						if first_date.split()[0] != (employee_attendance_record.name).split()[0]:
 							if list_for_same_date!= []:
 								signin_attendance_record = hr_attendance_obj.browse(cr,uid,[list_for_same_date[0]])
 								signout_attendance_record = hr_attendance_obj.browse(cr,uid,[list_for_same_date[-1]])
 								signin_attendance_record_update=datetime.strptime(signin_attendance_record.name, '%Y-%m-%d %H:%M:%S')
 								signout_attendance_record_update=datetime.strptime(signout_attendance_record.name, '%Y-%m-%d %H:%M:%S')
 								signin_attendance_record_utc = signin_attendance_record_update + timedelta(hours=5,minutes=30)
 								signout_attendance_record_utc = signout_attendance_record_update + timedelta(hours=5,minutes=30)
 								diff_in_time = signout_attendance_record_update - signin_attendance_record_update
 								vals = {
 									'name':(signin_attendance_record.name).split()[0],
 									'employee_id': signin_attendance_record.employee_id.id,
 									'sign_in' : str(signin_attendance_record_update),
 									'sign_out':str (signout_attendance_record_update),
 									'total_duration' : ((diff_in_time.seconds) / 60) / 60.0,

 								}
 								hr_attendance_record_obj.create(cr,uid,vals)

 							first_date = employee_attendance_record.name
 							list_for_same_date = []
 							list_for_same_date.append(employee_attendance_record.id)
 						else:
 							list_for_same_date.append(employee_attendance_record.id)
 				else:
 					today = datetime.today()
 					new_today = (today + timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
 					new_today_utc = datetime.strptime(new_today, '%Y-%m-%d %H:%M:%S')
 					attendance_report_last_record = hr_attendance_record_obj.browse(cr,uid,[attendance_report_record_status[0]])
 					last_first_record = attendance_report_last_record.name
 					datetime_attendance_record_date=datetime.strptime(attendance_report_last_record.name, '%Y-%m-%d')
 					datetime_attendace_record_signout = datetime.strptime(attendance_report_last_record.sign_out, '%Y-%m-%d %H:%M:%S')
 					last_attendance_record = hr_attendance_obj.browse(cr,uid,hr_attendance_search[-1])
 					datetime_last_attendace_date = datetime.strptime((last_attendance_record.name).split()[0], '%Y-%m-%d')
 					datetime_before_last_attendace_date = datetime_attendance_record_date + timedelta(1)
 					################ Check For last update to make it match for today############
 					today_for_date_only = datetime.strptime(today.strftime("%Y-%m-%d"),'%Y-%m-%d')
 					today_for_date = datetime.strptime((last_attendance_record.name).split()[0],"%Y-%m-%d") + timedelta()
 					before_last_original_attendance_search = hr_attendance_obj.search(cr,uid,[('name','<',str(today_for_date)),('employee_id','=',employee_list.id)])[0]
 					before_last_original_attendance_browse = hr_attendance_obj.browse(cr,uid,before_last_original_attendance_search)
 					before_last_original_date = datetime.strptime((before_last_original_attendance_browse.name).split()[0], '%Y-%m-%d')
 					datetime_second_last_attendace_date = ''
 					if before_last_original_date == datetime_attendance_record_date and  datetime_last_attendace_date == today_for_date_only :
 						diff = (datetime_last_attendace_date - before_last_original_date).days
 						datetime_second_last_attendace_date = datetime_attendance_record_date + timedelta(diff)
 					else:
 						datetime_second_last_attendace_date = datetime_attendance_record_date + timedelta(1)
 					#####################################################################################

 					###############Verifying last Record of Daily attendance Module#################
 					datetime_last_first_record = datetime.strptime(last_first_record,'%Y-%m-%d') + timedelta()
 					next_day_after_last_record = datetime_last_first_record + timedelta(1)
 					attendance_last_records_search = hr_attendance_obj.search(cr,uid,[('name','>',str(datetime_last_first_record)),('name','<',str(next_day_after_last_record)),('employee_id','=',employee_list.id)])[0]
 					attendance_last_records_browse = hr_attendance_obj.browse(cr, uid,[attendance_last_records_search])
 					if datetime.strptime(attendance_last_records_browse.name,'%Y-%m-%d %H:%M:%S') != datetime.strptime(attendance_report_last_record.sign_out,'%Y-%m-%d %H:%M:%S'):
 						signout_current_date_is = datetime.strptime(attendance_last_records_browse.name,'%Y-%m-%d %H:%M:%S') + timedelta(hours=5,minutes=30)
 						signin_current_date_is = datetime.strptime(attendance_report_last_record.sign_in,'%Y-%m-%d %H:%M:%S') + timedelta(hours=5,minutes=30)
 						check_total_diff = signout_current_date_is - signin_current_date_is
 						hr_attendance_record_obj.write(cr, uid, attendance_report_last_record.id, {'sign_out':attendance_last_records_browse.name,'total_duration':((check_total_diff.seconds) / 60) / 60.0})

 					###################################################
 					
 					if datetime_last_attendace_date >  datetime_attendance_record_date and str(datetime_second_last_attendace_date).split()[0] != new_today.split()[0]:
 						list_of_last_date_record = hr_attendance_obj.search(cr,uid,[('name','>',str(datetime_before_last_attendace_date)),('employee_id','=',employee_list.id)], order='name ASC')
 						if list_of_last_date_record != []:
 							list_for_same_date1 = []
 							for records in range(0,len(list_of_last_date_record)):
 								employee_attendance_record1 = hr_attendance_obj.browse(cr,uid,list_of_last_date_record[records])
 								if last_first_record != (employee_attendance_record1.name).split()[0]:
 									if list_for_same_date1 != []:
 										signin_attendance_record1 = hr_attendance_obj.browse(cr,uid,[list_for_same_date1[0]])
 										signout_attendance_record1 = hr_attendance_obj.browse(cr,uid,[list_for_same_date1[-1]])
 										signin_attendance_record_update1=datetime.strptime(signin_attendance_record1.name, '%Y-%m-%d %H:%M:%S')
 										signout_attendance_record_update1=datetime.strptime(signout_attendance_record1.name, '%Y-%m-%d %H:%M:%S')
 										diff_in_time1 = signout_attendance_record_update1 - signin_attendance_record_update1
 										vals1 = {
 											'name':(signin_attendance_record1.name).split()[0],
 											'employee_id': signin_attendance_record1.employee_id.id,
 											'sign_in' : str(signin_attendance_record_update1),
 											'sign_out':str (signout_attendance_record_update1),
 											'total_duration' : ((diff_in_time1.seconds) / 60) / 60.0,

 										}
 										hr_attendance_record_obj.create(cr,uid,vals1)
 									last_first_record = (employee_attendance_record1.name).split()[0]
 									list_for_same_date1 = []
 									list_for_same_date1.append(employee_attendance_record1.id)
 								else:
 									list_for_same_date1.append(employee_attendance_record1.id)	
 								

 					else :
 						if str(datetime_last_attendace_date).split()[0] == new_today.split()[0]:
 							today_check_for_record = datetime.strptime(new_today.split()[0], '%Y-%m-%d') + timedelta()
 							check_today_ids = hr_attendance_record_obj.search(cr,uid,[('employee_id','=',employee_list.id),('name','=',new_today.split()[0])])
 							list_of_last_date_record1 = hr_attendance_obj.search(cr,uid,[('name','>',str(today_check_for_record)),('employee_id','=',employee_list.id)])
 							signin_attendance_record_same_day = hr_attendance_obj.browse(cr,uid,[list_of_last_date_record1[-1]])
 							signout_attendance_record_same_day = hr_attendance_obj.browse(cr,uid,[list_of_last_date_record1[0]])
 							signin_attendance_record_same_day_update = datetime.strptime(signin_attendance_record_same_day.name, '%Y-%m-%d %H:%M:%S')
 							signout_attendance_record_same_day_update = datetime.strptime(signout_attendance_record_same_day.name, '%Y-%m-%d %H:%M:%S')
 							diff = (signout_attendance_record_same_day_update - signin_attendance_record_same_day_update)
 							new_diff = ((diff.seconds) / 60 ) / 60.0
 							if check_today_ids == []:
 								vals = {
 									'name': new_today.split()[0],
 									'employee_id': employee_list.id,
 									'sign_in' : str(signin_attendance_record_same_day_update),
 									'sign_out':str (signout_attendance_record_same_day_update),
 									'total_duration': new_diff,
 								}
 								new_record_attendance = hr_attendance_record_obj.create(cr,uid,vals)
 								previous_datetime_record_browse = hr_attendance_record_obj.browse(cr, uid, new_record_attendance)
 								previous_report_attendance_record = hr_attendance_record_obj.search(cr,uid,[('employee_id','=',employee_list.id),('name','<',previous_datetime_record_browse.name)])[0]
 								signout_report_attendance_record = hr_attendance_record_obj.browse(cr, uid, previous_report_attendance_record)
 								previous_datetime_record = datetime.strptime(signout_report_attendance_record.name,'%Y-%m-%d') + timedelta()
 								previous_original_attendance_record = hr_attendance_obj.search(cr,uid,[('name','>',str(previous_datetime_record)),('name','<',str(today_check_for_record)),('employee_id','=',employee_list.id)])[0]
 								signout_original_attendance_record =  hr_attendance_obj.browse(cr,uid,[previous_original_attendance_record])
 								if previous_report_attendance_record != []:
 									if datetime.strptime(signout_original_attendance_record.name,'%Y-%m-%d %H:%M:%S') !=  datetime.strptime(signout_report_attendance_record.sign_out,'%Y-%m-%d %H:%M:%S'):
 										correct_signout_date = datetime.strptime(signout_original_attendance_record.name,'%Y-%m-%d %H:%M:%S') + timedelta(hours=5,minutes=30)
 										correct_sigin_date = datetime.strptime(signout_report_attendance_record.sign_in,'%Y-%m-%d %H:%M:%S')  + timedelta(hours=5,minutes=30)
 										previous_diff = correct_signout_date - correct_sigin_date
 										hr_attendance_record_obj.write(cr, uid, previous_report_attendance_record, {'sign_out':signout_original_attendance_record.name,'total_duration':((previous_diff.seconds) / 60) / 60.0})

 							else:
 								hr_attendance_record_obj.write(cr,uid,check_today_ids,{'sign_out':str(signout_attendance_record_same_day_update),'total_duration' :new_diff})
 								
 		
 		return True				


 	def onchange_signout(self, cr, uid, ids, sign_in, sign_out,context=None):
 		vals = {'total_duration':0.0}
 		signin_format = datetime.strptime(sign_in, '%Y-%m-%d %H:%M:%S')
 		signout_format = datetime.strptime(sign_out, '%Y-%m-%d %H:%M:%S')
 		diff_time = signout_format - signin_format
 		vals.update({'total_duration':((diff_time.seconds) / 60) / 60.0})
 		return {'value':vals}


class company_public_holidays (osv.osv):
	_name = "company.public.holidays"
	_description = "Company Public Holidays"

	_columns = {
		'name': fields.char("Holiday Name", required=True),
		'holiday_day': fields.date("Date"),
		'holiday_weekday': fields.char("Week Days"),
		'record_year': fields.char("Year"),
		'company_ids':fields.many2many('res.company','company_public_holidays_rel', 'public_holiday_id','company_id',string='Companies'),


	}

	_defaults = {
 		'holiday_day':date.today().strftime('%Y-%m-%d'),
 	}
	_order = 'holiday_day asc'

	def onchange_holiday_day(self, cr, uid, ids, holiday_day ,context=None):
 		vals = {'holiday_weekday': '','record_year':''}
 		datetime_holiday = datetime.strptime(holiday_day, '%Y-%m-%d')
 		weekday_dictionary = {'Sun':'Sunday','Mon':'Monday','Tue':'Tuesday','Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday'}
 		complete_name = weekday_dictionary[datetime_holiday.strftime('%a')]
 		vals.update({'holiday_weekday':complete_name,'record_year':datetime_holiday.year})
 		return {'value':vals}