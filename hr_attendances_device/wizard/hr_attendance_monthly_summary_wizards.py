
import time
from datetime import datetime
from openerp.tools.translate import _
from openerp.osv import fields, osv


class hr_attendance_monthly_summary_wizards(osv.osv_memory):
    _name = 'hr_attendance.monthly.summary.wizards'
    _description = 'Monthly Attendance Report For Employee'
    _columns = {
        'monthly_status': fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),
        	('5','May'),('6','June'),('7','July'),('8','August'),('9','September'),('10','October'),('11','November'),('12','December')], 
        	'Select Month', required=False),
        'filter_by_date':fields.boolean('Filter By Date',help="Check this check box. To get report based on Date. Difference between From date and To Date will be 31 days(max)."),
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'emp_id':fields.many2many('hr.employee', 'summary_emp_attendance_rel', 'sum_id', 'emp_id', 'Employee(s)'),
    }

    _defaults = {
        'filter_by_date':False,
    }

    def onchange_date_to(self, cr, uid, ids, date_from , date_to, context=None):
        if date_from != False and date_to != False:
            new_date_from = datetime.strptime(date_from,'%Y-%m-%d')
            new_date_to = datetime.strptime(date_to,'%Y-%m-%d')
            difference = new_date_to - new_date_from
            if difference.days < 0 or difference.days > 31:
                raise osv.except_osv(_('Information'),_('Difference in Date from and Date To will not greater than 31 days.'))
        return True

    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context=context)[0]
        data['emp_id'] = context['active_ids']
        if data['date_from'] != False and data['date_to'] != False:
            new_date_from = datetime.strptime(data['date_from'],'%Y-%m-%d')
            new_date_to = datetime.strptime(data['date_to'],'%Y-%m-%d')
            difference = new_date_to - new_date_from
            if difference.days < 0 or difference.days > 31:
                raise osv.except_osv(_('Information'),_('Difference in Date from and Date To will not greater than 31 days.'))
                return False
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data,
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hr_attendance.monthly.summary',
            'datas': datas,
            }


