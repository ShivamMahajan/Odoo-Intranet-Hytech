# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 conexus (<http://conexus.at>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import socket, array, re, time

from openerp.osv import fields, osv
from openerp.tools.translate import _


class hr_attendance_terminal(osv.osv):
	_name = "hr.attendance.terminal"

	_columns = {
		'tnr': fields.char('Terminal Number', required=True, size=8, select=1, help='Input with two digits, e.g. 01'),
		'location': fields.char('Location', size=128, select=1),
		'ip': fields.char('IP Address',required=True, size=15, select=1),
		'license_nr': fields.char('License Number', required=True, size=12, select=1),
		'sign_in_hour': fields.char('Sign in Hour', size=2, required=True, select=1, help='Input with two digits, e.g. 08'),
		'sign_in_minute': fields.char('Sign in Minute', size=2, required=True, select=1, help='Input with two digits, e.g. 30'),
		'sign_out_hour': fields.char('Sign out Hour',size=2, required=True, select=1, help='Input with two digits, e.g. 08'),
		'sign_out_minute': fields.char('Sign in Minute',size=2, required=True, select=1, help='Input with two digits, e.g. 30'),
	}


	#BCC BlockCheckCharakter generieren:
	def create_bcc(self, teststring):
		
		testarray = [ord(c) for c in teststring]
		bccint = testarray[0]

		for bccint_item in testarray[1:]:
			bccint = bccint ^ bccint_item 

		str_hex_bcc = str(hex(bccint))
		str_bcc = re.sub(r'0x', '', str_hex_bcc)

		return str_bcc

	#Terminals auslesen
	def fetch_attendance_records(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
	        if context is None:
			context = {}

		terminal_ids = self.pool.get('hr.attendance.terminal').search(cr, uid, [])
		for t_id in terminal_ids:
			terminal = self.pool.get('hr.attendance.terminal').browse(cr, uid, t_id, context=context)
			print "FETCH ATTENDANCE RECORDS FROM Terminal: %s | %s" % (terminal.tnr, terminal.ip)

			TerminalNr = terminal.tnr # zweistelling in Hex			
			host = terminal.ip # Terminaladresse
			port = 4370 # Terminaldatenport
			STX = '\x02' # Startbit
			ETX = '\x03' # Stopbit


			#Verbindung herstellen
			s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			try:
				s.connect((host,port))
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break


			#Paket / Telegram erstellen
			#Schema: <STX>SS<Kommando><Daten><BCC><ETX>

			bccstring = self.create_bcc(TerminalNr + 'ABSTD')
			message = STX + TerminalNr + 'ABSTD' + bccstring + ETX
			print ("Message send to the server is ---"),message
			#Paket / Telegram senden
			try:
				s.sendall(message)
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break


			#EMPFANGEN
			#Beispiel Antwort mit Stempelung: \x0201ABSTD0000000192772226KO270420110958004C\x03
			#Beispiel Sende LÖSTD: \x0201L\x99STD0000000493\x03
			while 1:
				try:
					reply = s.recv(8192)
					print ("Reply from the server is"),reply
					if str(reply) != '':
						r_message = re.sub(r'\x02|\x03','',str(reply))
						r_terminal = r_message[0:2]
						#print "Terminal Nr: %s" % r_terminal
						#print "Message: %s" % r_message [2:15]
						if r_message[2:15] == 'ABSTD00000000':
							print "Keine Stempelungen vorhanden!"
							break
						else:
							if r_message [2:7] == 'ABSTD':
						
								r_number = r_message[7:15]
								r_rfid_key = r_message[15:23]
								r_reason = r_message[23:25]
								r_datetime_str = r_message[25:39]
								r_datetime = time.strptime(r_datetime_str, "%d%m%Y%H%M%S")
								t_stamp = time.mktime(r_datetime)
								t_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_stamp))
								#print "--- REC START ---"
								#print "Attendance Record Nr: %s | RFID Key: %s | Reason: %s | Datetime: %s" % (r_number, r_rfid_key, r_reason, t_stamp) 
								#print "--- REC END ---"

								emp_id = self.pool.get('hr.employee').search(cr, uid, [('rfid_key', '=', r_rfid_key)])
								if emp_id:
									employee = self.pool.get('hr.employee').browse(cr, uid, emp_id, context=context)[0]
									#print "Employee: %s" % employee.name

								if r_reason == 'KO':
									r_reason = 'sign_in'
								if r_reason == 'GE':
									r_reason = 'sign_out'
								attendance = self.pool.get('hr.attendance')
								attendance_record = {
									'employee_id' : employee.resource_id.id,
									'action' : r_reason,
									'name' : t_stamp
								}



								attendance.create(cr, uid, attendance_record)

							
								bccstring = self.create_bcc(r_terminal + 'L\x99STD' + r_number) 
								message = STX + r_terminal + 'L\x99STD' + r_number + bccstring + ETX

								try:
									s.sendall(message)
								except socket.error, msg:
									print 'Socket Error: %s' % msg

						if r_message[2:7] == 'L\x99STD':
								#print "---DELETION CONFIRMED---"
								TerminalNr = '01' # zweistelling in Hex
								bccstring = self.create_bcc(TerminalNr + 'ABSTD')
								message = STX + TerminalNr + 'ABSTD' + bccstring + ETX
								s.sendall(message)

				except socket.error, msg:
					print 'Socket Error: %s' % msg
					break
			s.close()
		return True



	#User an Terminals senden
	def create_terminal_users(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
	        if context is None:
			context = {}

		terminal_ids = self.pool.get('hr.attendance.terminal').search(cr, uid, [])

		for t_id in terminal_ids:
			terminal = self.pool.get('hr.attendance.terminal').browse(cr, uid, t_id, context=context)
			#print "CREATE USER ON Terminal: %s | %s" % (terminal.tnr, terminal.ip)

			TerminalNr = terminal.tnr # zweistelling in Hex			
			host = terminal.ip # Terminaladresse

			port = 4370 # Terminaldatenport
			STX = '\x02' # Startbit
			ETX = '\x03' # Stopbit

			emp_ids = self.pool.get('hr.employee').search(cr, uid, [('rfid_key', '!=', '')])
			if emp_ids:

				#Verbindung herstellen
				s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
				try:
					s.connect((host,port))
				except socket.error, msg:
					print 'Socket Error: %s' % msg
					break

				for emp_id in emp_ids:
					employee = self.pool.get('hr.employee').browse(cr, uid, emp_id, context=context)
			
					rfid_key = employee.rfid_key
					employee_name = employee.name
					pin = '0000'
					pinabfrage = '0' # bei 1 wird pin abgefragt
					infotext1 = '                ' # 16 Zeichen Infotext
					infotext2 = employee_name.center(16) # 16 Zeichen Infotext
					infotext3 = '                ' # 16 Zeichen Infotext
					infotext4 = '                ' # 16 Zeichen Infotext

					#Paket / Telegram erstellen
					#Schema: <STX>SS<Kommando><Daten><BCC><ETX>

					bccstring = self.create_bcc(TerminalNr + 'SPSTA' + rfid_key + pin + pinabfrage + infotext1 + infotext2 + infotext3 + infotext4)
					message = STX + TerminalNr + 'SPSTA' + rfid_key + pin + pinabfrage + infotext1 + infotext2 + infotext3 + infotext4 + bccstring + ETX
					#print "Employee: %s" % employee.name
					#Paket / Telegram senden
					try:
						s.sendall(message)
					except socket.error, msg:
						print 'Socket Error: %s' % msg
						break
					while 1:
						reply = s.recv(8192)
						if str(reply) != '':
							r_message = re.sub(r'\x02|\x03','',str(reply))
							r_terminal = r_message[0:2]
							if r_message[2:7] == 'SPSTA':
								#print "Stammsatz gespeichert!"
								break

				s.close()
		return True

	#Zeit setzen
	def set_terminal_time(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
	        if context is None:
			context = {}

		terminal_ids = self.pool.get('hr.attendance.terminal').search(cr, uid, [])
		for t_id in terminal_ids:
			terminal = self.pool.get('hr.attendance.terminal').browse(cr, uid, t_id, context=context)

			#print "SET TIME ON Terminal: %s | %s" % (terminal.tnr, terminal.ip)

			TerminalNr = terminal.tnr # zweistelling in Hex			
			host = terminal.ip # Terminaladresse

			port = 8000 # Terminaldatenport
			STX = '\x02' # Startbit
			ETX = '\x03' # Stopbit

			#SENDEN
			#Verbindung herstellen
			s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			try:
				s.connect((host,port))
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break

			# BEISPIEL Uhr Telegram 01STUHR20110503209191199999999999999999999999999997E

			datetime_str = time.strftime('%Y%m%d%w%H%M%S')                    
			bccstring = self.create_bcc(TerminalNr + 'STUHR' + datetime_str + '9999999999999999999999999999')
			message = STX + TerminalNr + 'STUHR' + datetime_str + '9999999999999999999999999999' + bccstring + ETX

			#Paket / Telegram senden
			try:
				s.sendall(message)
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break
				

			while 1:
				try:
					reply = s.recv(8192)
					if str(reply) != '':
						r_message = re.sub(r'\x02|\x03','',str(reply))
						r_terminal = r_message[0:2]

						if r_message[2:7] == 'STUHR':
							#print "Zeit gespeichert!"
							break

				except socket.error, msg:
					print 'Socket Error: %s' % msg
					break

		s.close()
		return True


	#Automatische Funktionsvorgabe - Kommen / Gehenfunktion wird zeitgesteuert gesetzt
	def set_signinout_times(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
	        if context is None:
			context = {}

		terminal_ids = self.pool.get('hr.attendance.terminal').search(cr, uid, [])

		for t_id in terminal_ids:
			terminal = self.pool.get('hr.attendance.terminal').browse(cr, uid, t_id, context=context)
			#print "SET Sign In/Out Times Terminal: %s | %s" % (terminal.tnr, terminal.ip)

			TerminalNr = terminal.tnr # zweistelling in Hex			
			host = terminal.ip # Terminaladresse
			signin_time =  "%.4X" % (int(terminal.sign_in_hour) * 60 + int(terminal.sign_in_minute))
			signout_time = "%.4X" % (int(terminal.sign_out_hour) * 60 + int(terminal.sign_out_minute))
			#print "SIGN IN TIME: %s | SIGN OUT TIME %s" % (signin_time, signout_time)
			port = 8000 # Terminaldatenport
			STX = '\x02' # Startbit
			ETX = '\x03' # Stopbit

			#SENDEN
			#Verbindung herstellen
			s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			try:
				s.connect((host,port))
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break

			datetime_str = time.strftime('%d.%m.%Y %H:%M:%S')               

			bccstring = self.create_bcc(TerminalNr + 'SPCFG' + 'Terminaleinstellungsdatei ADC Terminaltyp : OT02\x0d\x0aErstellt am ' + datetime_str + '\x0d\x0aOT02\x0d\x0aB01C4D0E0F4I0G8192838485H1J0K0L11111111M1111111N11111111O000000000000000000000000000000000000000000000000000000000000000P0Q2AR05T3131313U00V0W1Y112222220100000Z0#50*' + host + '>255.255.255.000\x0d\x0a+000FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00-' + signin_time + '91' + signout_time + '92FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00&' + terminal.license_nr + '!0A\x0d\x0a')
			message = STX + TerminalNr + 'SPCFG' + 'Terminaleinstellungsdatei ADC Terminaltyp : OT02\x0d\x0aErstellt am ' + datetime_str + '\x0d\x0aOT02\x0d\x0aB01C4D0E0F4I0G8192838485H1J0K0L11111111M1111111N11111111O000000000000000000000000000000000000000000000000000000000000000P0Q2AR05T3131313U00V0W1Y112222220100000Z0#50*' + host + '>255.255.255.000\x0d\x0a+000FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00-' + signin_time + '91' + signout_time + '92FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00FFFF00&' + terminal.license_nr + '!0A\x0d\x0a' + bccstring + ETX
			#print bccstring

			#Paket / Telegram senden
			try:
				s.sendall(message)
			except socket.error, msg:
				print 'Socket Error: %s' % msg
				break
				

			while 1:
				try:
					reply = s.recv(8192)
					if str(reply) != '':
						r_message = re.sub(r'\x02|\x03','',str(reply))
						r_terminal = r_message[0:2]

						if r_message[2:7] == 'SPCFG':
							#print "Konfiguration gespeichert!"
							break

				except socket.error, msg:
					print 'Socket Error: %s' % msg
					break

		s.close()
		return True

	def _check_time_format(self, cr, uid, ids, context=None):
		terminal = self.read(cr, uid, ids, ['sign_in_hour','sign_in_minute','sign_out_hour','sign_out_minute'])
		regex = re.compile("([01]?[0-9]|2[0-3]):[0-5][0-9]")
		if regex.match(terminal[0]['sign_in_hour'] + ':' + terminal[0]['sign_in_minute']) and regex.search(terminal[0]['sign_out_hour'] + ':' + terminal[0]['sign_out_minute']):
			return True
		return False

	_constraints = [
		(_check_time_format, 'Please check the Sign In Hour Value!', ['sign_in_hour']),
		(_check_time_format, 'Please check the Sign In Minute Value!', ['sign_in_minute']),
		(_check_time_format, 'Please check the Sign Out Hour Value!', ['sign_out_hour']),
		(_check_time_format, 'Please check the Sign Out Minute Value!', ['sign_out_minute']),
	]
	_sql_constraints = [('tnr_uniq','unique(tnr)', 'Terminal Nr. must be unique!')]

hr_attendance_terminal()

