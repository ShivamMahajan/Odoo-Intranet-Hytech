# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
import pytz
from openerp import SUPERUSER_ID

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

class hr_timesheet_sheet(osv.osv):
    _name = "hr_timesheet_sheet.sheet"
    _inherit = "mail.thread"
    _table = 'hr_timesheet_sheet_sheet'
    _order = "id desc"
    _description="Timesheet"

    def _total(self, cr, uid, ids, name, args, context=None):
        """ Compute the attendances, analytic lines timesheets and differences between them
            for all the days of a timesheet and the current day
        """

        res = {}
        for sheet in self.browse(cr, uid, ids, context=context or {}):
            res.setdefault(sheet.id, {
                'total_attendance': 0.0,
                'total_timesheet': 0.0,
                'total_difference': 0.0,
            })
            for period in sheet.period_ids:
                res[sheet.id]['total_attendance'] += period.total_attendance
                res[sheet.id]['total_timesheet'] += period.total_timesheet
                res[sheet.id]['total_difference'] += period.total_attendance - period.total_timesheet
        return res

    def check_employee_attendance_state(self, cr, uid, sheet_id, context=None):
        ids_signin = self.pool.get('hr.attendance').search(cr,uid,[('sheet_id', '=', sheet_id),('action','=','sign_in')])
        ids_signout = self.pool.get('hr.attendance').search(cr,uid,[('sheet_id', '=', sheet_id),('action','=','sign_out')])

        #if len(ids_signin) != len(ids_signout):
        #  raise osv.except_osv(('Warning!'),_('The timesheet cannot be validated as it does not contain an equal number of sign ins and sign outs.'))
        return True

    def copy(self, cr, uid, ids, *args, **argv):
        raise osv.except_osv(_('Error!'), _('You cannot duplicate a timesheet.'))

    def create(self, cr, uid, vals, context=None):
        if 'employee_id' in vals:
            if not self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).user_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link him/her to a user.'))
            if not self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).product_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link the employee to a product, like \'Consultant\'.'))
            if not self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).journal_id:
                raise osv.except_osv(_('Configuration Error!'), _('In order to create a timesheet for this employee, you must assign an analytic journal to the employee, like \'Timesheet Journal\'.'))
        if vals.get('attendances_ids'):
            # If attendances, we sort them by date asc before writing them, to satisfy the alternance constraint
            vals['attendances_ids'] = self.sort_attendances(cr, uid, vals['attendances_ids'], context=context)
        ### Description Validation
        timesheet_desc = vals.get('timesheet_ids')
        for len_des in range(1,len(timesheet_desc)):
            if timesheet_desc[len_des][2]['name'] == '/':
                raise osv.except_osv(_('Warning!'), _('Timesheet cannot be save unless Description field in Detail Tab having some context.'))
        ##########
        return super(hr_timesheet_sheet, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        #########---Put domain for Self Approval------- ###############
        if 'state' in vals:
            if len(ids) == 1:
                sheet_id = self.browse(cr,uid,ids)
                if uid == sheet_id.user_id.id and sheet_id.state=='confirm':
                    if vals['state'] == 'draft' or vals['state'] == 'done':
                        raise osv.except_osv(_('Warning!'), _('You are not allow to Approve/Refuse your own Timesheet.'))
                        vals.update({'state':'confirm'})

        ################################################################
        if 'employee_id' in vals:
            new_user_id = self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).user_id.id or False
            if not new_user_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link him/her to a user.'))
            if not self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).product_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link the employee to a product.'))
            if not self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context).journal_id:
                raise osv.except_osv(_('Configuration Error!'), _('In order to create a timesheet for this employee, you must assign an analytic journal to the employee, like \'Timesheet Journal\'.'))
    ###### Changed made to resolve overlap of timesheet##############
        if not self._sheet_date(cr, uid, ids, forced_user_id=uid, context=context):
                raise osv.except_osv(_('Error!'), _('You cannot have 2 timesheets that overlap!\nYou should use the menu \'My Timesheet\' to avoid this problem.'))
        if vals.get('attendances_ids'):
            # If attendances, we sort them by date asc before writing them, to satisfy the alternance constraint
            # In addition to the date order, deleting attendances are done before inserting attendances
            vals['attendances_ids'] = self.sort_attendances(cr, uid, vals['attendances_ids'], context=context)
        res = super(hr_timesheet_sheet, self).write(cr, uid, ids, vals, context=context)
        ########## Validation for timesheet description
        if 'timesheet_ids' in vals:
            timesheet_desc = vals.get('timesheet_ids')
            if len(timesheet_desc)==1:
                if timesheet_desc[0][2]['name'] == '/':
                    raise osv.except_osv(_('Warning!'), _('Timesheet cannot be save unless Description field in Detail Tab having some context.'))
            else:
                for len_des in range(0,len(timesheet_desc)):
                    if timesheet_desc[len_des][2] != False:
                        if 'name' in timesheet_desc[len_des][2]:
                            if timesheet_desc[len_des][2]['name'] == '/':
                                raise osv.except_osv(_('Warning!'), _('Timesheet cannot be save unless Description field in Detail Tab having some context.'))
        ################### Validation End #############
        ############# Remove Cheking For Attendance Device Integration
       # if vals.get('attendances_ids'):
        #    for timesheet in self.browse(cr, uid, ids):
        #       if not self.pool['hr.attendance']._altern_si_so(cr, uid, [att.id for att in timesheet.attendances_ids]):
         #           raise osv.except_osv(_('Warning !'), _('Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)'))
        return res

    def sort_attendances(self, cr, uid, attendance_tuples, context=None):
        date_attendances = []
        for att_tuple in attendance_tuples:
            if att_tuple[0] in [0,1,4]:
                if att_tuple[0] in [0,1]:
                    if att_tuple[2] and att_tuple[2].has_key('name'):
                        name = att_tuple[2]['name']
                    else:
                        name = self.pool['hr.attendance'].browse(cr, uid, att_tuple[1]).name
                else:
                    name = self.pool['hr.attendance'].browse(cr, uid, att_tuple[1]).name
                date_attendances.append((1, name, att_tuple))
            elif att_tuple[0] in [2,3]:
                date_attendances.append((0, self.pool['hr.attendance'].browse(cr, uid, att_tuple[1]).name, att_tuple))
            else: 
                date_attendances.append((0, False, att_tuple))
        date_attendances.sort()
        return [att[2] for att in date_attendances]

    def button_confirm(self, cr, uid, ids, context=None):
        for sheet in self.browse(cr, uid, ids, context=context):
            if sheet.employee_id and sheet.employee_id.parent_id and sheet.employee_id.parent_id.user_id:
                self.message_subscribe_users(cr, uid, [sheet.id], user_ids=[sheet.employee_id.parent_id.user_id.id], context=context)
            self.check_employee_attendance_state(cr, uid, sheet.id, context=context)
            di = sheet.user_id.company_id.timesheet_max_difference
            if (abs(sheet.total_difference) < di) or not di:
                sheet.signal_workflow('confirm')
                self.timesheet_submit_notificate(cr, uid, ids, context=context)
            else:
                raise osv.except_osv(_('Warning!'), _('Please verify that the total difference of the sheet is lower than %.2f.') %(di,))
            ###############--Showing Warning when submitting timesheet before week completion----########
            Today =datetime.today() + relativedelta(days=1)
            date_to = datetime.strptime(sheet.date_to,'%Y-%m-%d')
            today = datetime.strptime(str(Today).split()[0],'%Y-%m-%d')
            if date_to > today:
                raise osv.except_osv(_('Warning!'), _('You are not allowed to submit this week timesheet before ending the week i.e. %s') %(sheet.date_to))
            #########################################################################
        return True

    def timesheet_submit_notificate(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            self.message_post(cr, uid, [obj.id],
                _("Timesheet submitted for approval by your subordinate %s")%(obj.employee_id.name), context=context)

    def attendance_action_change(self, cr, uid, ids, context=None):
        hr_employee = self.pool.get('hr.employee')
        employee_ids = []
        for sheet in self.browse(cr, uid, ids, context=context):
            if sheet.employee_id.id not in employee_ids: employee_ids.append(sheet.employee_id.id)
        return hr_employee.attendance_action_change(cr, uid, employee_ids, context=context)
    
    def _count_all(self, cr, uid, ids, field_name, arg, context=None):
        Timesheet = self.pool['hr.analytic.timesheet']
        Attendance = self.pool['hr.attendance']
        return {
            sheet_id: {
                'timesheet_activity_count': Timesheet.search_count(cr,uid, [('sheet_id','=', sheet_id)], context=context),
                'attendance_count': Attendance.search_count(cr,uid, [('sheet_id', '=', sheet_id)], context=context)
            }
            for sheet_id in ids
        }

    _columns = {
        'name': fields.char('Note', select=1,
                            states={'confirm':[('readonly', True)], 'done':[('readonly', True)]}),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True,readonly=True),
        'user_id': fields.related('employee_id', 'user_id', type="many2one", relation="res.users", store=True, string="User", required=False, readonly=True),#fields.many2one('res.users', 'User', required=True, select=1, states={'confirm':[('readonly', True)], 'done':[('readonly', True)]}),
        'date_from': fields.date('Date from', required=True, select=1, readonly=True, states={'new':[('readonly', False)]}),
        'date_to': fields.date('Date to', required=True, select=1, readonly=True, states={'new':[('readonly', False)]}),
        'timesheet_ids' : fields.one2many('hr.analytic.timesheet', 'sheet_id',
            'Timesheet lines',
            readonly=True, states={
                'draft': [('readonly', False)],
                'new': [('readonly', False)]}
            ),
        'attendances_ids' : fields.one2many('hr.attendance', 'sheet_id', 'Attendances'),
        'state' : fields.selection([
            ('new', 'New'),
            ('draft','Open'),
            ('confirm','Waiting Approval'),
            ('done','Approved')], 'Status', select=True, required=True, readonly=True,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed timesheet. \
                \n* The \'Confirmed\' status is used for to confirm the timesheet by user. \
                \n* The \'Done\' status is used when users timesheet is accepted by his/her senior.'),
        'state_attendance' : fields.related('employee_id', 'state', type='selection', selection=[('absent', 'Absent'), ('present', 'Present')], string='Current Status', readonly=True),
        'total_attendance': fields.function(_total, method=True, string='Total Attendance', multi="_total"),
        'total_timesheet': fields.function(_total, method=True, string='Total Timesheet', multi="_total"),
        'total_difference': fields.function(_total, method=True, string='Difference', multi="_total"),
        'period_ids': fields.one2many('hr_timesheet_sheet.sheet.day', 'sheet_id', 'Period', readonly=True),
        'account_ids': fields.one2many('hr_timesheet_sheet.sheet.account', 'sheet_id', 'Analytic accounts', readonly=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'department_id':fields.many2one('hr.department','Department'),
        'timesheet_activity_count': fields.function(_count_all, type='integer', string='Timesheet Activities', multi=True),
        'attendance_count': fields.function(_count_all, type='integer', string="Attendances", multi=True),
    }

   

    def _default_date_from(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return time.strftime('%Y-%m-01')
        elif r=='week':
            return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r=='year':
            return time.strftime('%Y-01-01')
        return time.strftime('%Y-%m-%d')

    def _default_date_to(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return (datetime.today() + relativedelta(months=+1,day=1,days=-1)).strftime('%Y-%m-%d')
        elif r=='week':
            return (datetime.today() + relativedelta(weekday=4)).strftime('%Y-%m-%d')
        elif r=='year':
            return time.strftime('%Y-12-31')
        return time.strftime('%Y-%m-%d')

    def _default_employee(self, cr, uid, context=None):
        emp_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        return emp_ids and emp_ids[0] or False

    _defaults = {
        'date_from' : _default_date_from,
        'date_to' : _default_date_to,
        'state': 'new',
        'employee_id': _default_employee,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'hr_timesheet_sheet.sheet', context=c)
    }

    def _sheet_date(self, cr, uid, ids, forced_user_id=False, context=None):
        for sheet in self.browse(cr, uid, ids, context=context):
            new_user_id = sheet.user_id and sheet.user_id.id #forced_user_id or 
            if new_user_id:
                cr.execute('SELECT id \
                    FROM hr_timesheet_sheet_sheet \
                    WHERE (date_from <= %s and %s <= date_to) \
                        AND user_id=%s \
                        AND id <> %s',(sheet.date_to, sheet.date_from, new_user_id, sheet.id))
                if cr.fetchall():
                    return False
        return True


    _constraints = [
        (_sheet_date, 'You cannot have 2 timesheets that overlap!\nPlease use the menu \'My Current Timesheet\' to avoid this problem.', ['date_from','date_to']),
    ]

    def action_set_to_draft(self, cr, uid, ids, *args):

        self.write(cr, uid, ids, {'state': 'draft'})
        self.create_workflow(cr, uid, ids)
        return True

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        return [(r['id'], _('Week ')+datetime.strptime(r['date_from'], '%Y-%m-%d').strftime('%U')) \
                for r in self.read(cr, uid, ids, ['date_from'],
                    context=context, load='_classic_write')]

    def unlink(self, cr, uid, ids, context=None):
        sheets = self.read(cr, uid, ids, ['state','total_attendance'], context=context)
        for sheet in sheets:
            if sheet['state'] in ('confirm', 'done'):
                raise osv.except_osv(_('Invalid Action!'), _('You cannot delete a timesheet which is already confirmed.'))
            elif sheet['total_attendance'] <> 0.00:
                raise osv.except_osv(_('Invalid Action!'), _('You cannot delete a timesheet which have attendance entries.'))
        return super(hr_timesheet_sheet, self).unlink(cr, uid, ids, context=context)

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        department_id =  False
        user_id = False
        #project_obj = self.pool.get('project.project')
        #analytic_obj = self.pool.get('account.analytic.account')
        if employee_id:
            empl_id = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
            department_id = empl_id.department_id.id
            user_id = empl_id.user_id.id
           # employee_related_project = project_obj.search(cr,uid,['|',('members', '=', user_id),('user_id','=',user_id)],context=context)
           # analytical_account_project = []
            #for emp_project in project_obj.browse(cr,uid,employee_related_project,context):
             #   analytical_account_project.append(emp_project.analytic_account_id.id)
            #return {'value': {'department_id': department_id, 'user_id': user_id},'domain':{'account_id':[('id','in',analytical_account_project)],'account':[('id','in',analytical_account_project)]}}
        #return {'domain': {'account_id':[('id','in',analytical_account_project)],'account':[('id','in',analytical_account_project)]}}
        return {'value': {'department_id': department_id, 'user_id': user_id}}

    

    # ------------------------------------------------
    # OpenChatter methods and notifications
    # ------------------------------------------------

    def _needaction_domain_get(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        empids = emp_obj.search(cr, uid, [('parent_id.user_id', '=', uid)], context=context)
        if not empids:
            return False
        dom = ['&', ('state', '=', 'confirm'), ('employee_id', 'in', empids)]
        return dom


class account_analytic_line(osv.osv):
    _inherit = "account.analytic.line"

    def _get_default_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        #get the default date (should be: today)
        res = super(account_analytic_line, self)._get_default_date(cr, uid, context=context)
        #if we got the dates from and to from the timesheet and if the default date is in between, we use the default
        #but if the default isn't included in those dates, we use the date start of the timesheet as default
        if context.get('timesheet_date_from') and context.get('timesheet_date_to'):
            if context['timesheet_date_from'] <= res <= context['timesheet_date_to']:
                return res
            return context.get('timesheet_date_from')
        #if we don't get the dates from the timesheet, we return the default value from super()
        return res

class account_analytic_account(osv.osv):
    _inherit = "account.analytic.account"
    
    def name_create(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        group_template_required = self.pool['res.users'].has_group(cr, uid, 'account_analytic_analysis.group_template_required')
        if not context.get('default_use_timesheets') or group_template_required:
            return super(account_analytic_account, self).name_create(cr, uid, name, context=context)
        rec_id = self.create(cr, uid, {self._rec_name: name}, context)
        return self.name_get(cr, uid, [rec_id], context)[0]

    _defaults = {
        'account':1,
    }
class hr_timesheet_line(osv.osv):
    _inherit = "hr.analytic.timesheet"

    def _sheet(self, cursor, user, ids, name, args, context=None):
        sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
        res = {}.fromkeys(ids, False)
        for ts_line in self.browse(cursor, user, ids, context=context):
            sheet_ids = sheet_obj.search(cursor, user,
                [('date_to', '>=', ts_line.date), ('date_from', '<=', ts_line.date),
                 ('employee_id.user_id', '=', ts_line.user_id.id)],
                context=context)
            if sheet_ids:
            # [0] because only one sheet possible for an employee between 2 dates
                res[ts_line.id] = sheet_obj.name_get(cursor, user, sheet_ids, context=context)[0]
        return res

    def run_timesheet_log_by_employee(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        timesheet_record_obj = self.pool.get('hr.analytic.timesheet')
        employee_record_obj = self.pool.get('hr.employee')
        company_obj = self.pool.get('res.company')
        date_today = str(datetime.today()).split()[0]
        DATETIME_FORMAT = "%Y-%m-%d"
        add_row = ''
        add_row_never = ''
        body_part_company = ''
        for company_id in company_obj.search(cr,uid,[('parent_id','=',False)], context=context):
            company_name = company_obj.browse(cr, uid, company_id).name
            employee_record_search =  employee_record_obj.search(cr,uid,[('active','=',True),('user_id','!=',1),('company_id','=',company_id)])
            for employee_list in employee_record_obj.browse(cr,uid,employee_record_search):
                if employee_list.user_id :
                    timesheet_record_search=timesheet_record_obj.search(cr,uid,[('user_id','=',employee_list.user_id.id)])
                if timesheet_record_search == [] :
                    add_row_never += '''<tr bgcolor="#d7e9fa"><td> %s </td> </tr>'''%(employee_list.name)
                else :
                    last_update_date=timesheet_record_obj.browse(cr,uid,[timesheet_record_search[-1]])
                    from_dt = datetime.strptime(last_update_date.date, DATETIME_FORMAT)
                    to_dt = datetime.strptime(date_today, DATETIME_FORMAT)
                    if from_dt.strftime('%a') == 'Fri':
                        timedelta = (to_dt - from_dt).days - 2
                    else:
                        timedelta = (to_dt - from_dt).days
                    if timedelta > 0 :
                        add_row += '''<tr bgcolor="#d7e9fa"><td> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> <td style="border-right: 1px solid #ccc;text-align: center;"> %s </td> </tr>''' %(employee_list.name,str(timedelta).split(',')[0],last_update_date.date)
            #########Create Body part for Different Company ############
            body_part_company += ''' <div><h4 style="background: rgb(51,255,153);"> %s Company Timesheet Log</h4>
                            <table>
                            <caption><b>Employee who are not punctual in filling Timesheet</b></caption>
                                <thead>
                                    <tr bgcolor="#f2f3f2">
                                        <th style="width:24%%">Employee Name </th>
                                        <th style="border-right: 1px solid #ccc;"> Duration </th>
                                        <th style="border-right: 1px solid #ccc;"> Last Update </th>
                                    </tr>
                                </thead>
                                <tbody>
                                        %s
                                </tbody>
                            </table>
                            <table style = "margin-top:5%%">
                            <caption><b>Employee who never Fill the Timesheet</b></caption>
                                <thead>
                                    <tr bgcolor="#f2f3f2">
                                        <th style="width:24%%">Employee Name </th>
                                    </tr>
                                </thead>
                                <tbody>
                                        %s
                                </tbody>
                            </table>
                        </div> '''%(company_name,add_row,add_row_never)

            add_row = ''
            add_row_never = ''
            #######################################################

        body_html = '''<html>
                        <head></head>
                        <body>
                        <p> Hi,</p>
                        <p> Below are the TimeSheet exception Log send by Intranet</p>
                        %s
                        </body>
                        </html>
                        ''' %(body_part_company)

        sub = 'Employee Timesheet Exceptional Log From Intranet' 
        irconfig_obj = self.pool['ir.config_parameter']
        email_from = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.analytic.timesheet.email_from')
        email_to = irconfig_obj.get_param(cr, SUPERUSER_ID, 'hr.analytic.timesheet.email_to')
        vals = {'state': 'outgoing',
            'subject': sub,
            'body_html': '<pre>%s</pre>' % body_html,
            'email_to': email_to,
            'email_from': email_from,
           }
        if datetime.today().strftime('%a') == 'Sat' or datetime.today().strftime('%a') == 'Sun': 
            pass
        else:
            
            self.pool.get('mail.mail').create(cr, uid, vals, context=context)
        return True


    def _get_hr_timesheet_sheet(self, cr, uid, ids, context=None):
        ts_line_ids = []
        for ts in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                    SELECT l.id
                        FROM hr_analytic_timesheet l
                    INNER JOIN account_analytic_line al
                        ON (l.line_id = al.id)
                    WHERE %(date_to)s >= al.date
                        AND %(date_from)s <= al.date
                        AND %(user_id)s = al.user_id
                    GROUP BY l.id""", {'date_from': ts.date_from,
                                        'date_to': ts.date_to,
                                        'user_id': ts.employee_id.user_id.id,})
            ts_line_ids.extend([row[0] for row in cr.fetchall()])
        return ts_line_ids

    def _get_account_analytic_line(self, cr, uid, ids, context=None):
        ts_line_ids = self.pool.get('hr.analytic.timesheet').search(cr, uid, [('line_id', 'in', ids)])
        return ts_line_ids

    _columns = {
        'sheet_id': fields.function(_sheet, string='Sheet', select="1",
            type='many2one', relation='hr_timesheet_sheet.sheet', ondelete="cascade",
            store={
                    'hr_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                    'account.analytic.line': (_get_account_analytic_line, ['user_id', 'date'], 10),
                    'hr.analytic.timesheet': (lambda self,cr,uid,ids,context=None: ids, None, 10),
                  },
            ),
    }

    def _check_sheet_state(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for timesheet_line in self.browse(cr, uid, ids, context=context):
            if timesheet_line.sheet_id and timesheet_line.sheet_id.state not in ('draft', 'new'):
                return False
        return True

    _constraints = [
        (_check_sheet_state, 'You cannot modify an entry in a Confirmed/Done timesheet !', ['state']),
    ]

    def unlink(self, cr, uid, ids, *args, **kwargs):
        if isinstance(ids, (int, long)):
            ids = [ids]
        self._check(cr, uid, ids)
        return super(hr_timesheet_line,self).unlink(cr, uid, ids,*args, **kwargs)

    def _check(self, cr, uid, ids):
        for att in self.browse(cr, uid, ids):
            if att.sheet_id and att.sheet_id.state not in ('draft', 'new'):
                raise osv.except_osv(_('Error!'), _('You cannot modify an entry in a confirmed timesheet.'))
        return True

    def multi_on_change_account_id(self, cr, uid, ids, account_ids, context=None):
        return dict([(el, self.on_change_account_id(cr, uid, ids, el, context.get('user_id', uid))) for el in account_ids])



class hr_attendance(osv.osv):
    _inherit = "hr.attendance"

    def _get_default_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'name' in context:
            return context['name'] + time.strftime(' %H:%M:%S')
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def _get_hr_timesheet_sheet(self, cr, uid, ids, context=None):
        attendance_ids = []
        for ts in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                        SELECT a.id
                          FROM hr_attendance a
                         INNER JOIN hr_employee e
                               INNER JOIN resource_resource r
                                       ON (e.resource_id = r.id)
                            ON (a.employee_id = e.id)
                        WHERE %(date_to)s >= date_trunc('day', a.name)
                              AND %(date_from)s <= a.name
                              AND %(user_id)s = r.user_id
                         GROUP BY a.id""", {'date_from': ts.date_from,
                                            'date_to': ts.date_to,
                                            'user_id': ts.employee_id.user_id.id,})
            attendance_ids.extend([row[0] for row in cr.fetchall()])
        return attendance_ids

    def _get_attendance_employee_tz(self, cr, uid, employee_id, date, context=None):
        """ Simulate timesheet in employee timezone

        Return the attendance date in string format in the employee
        tz converted from utc timezone as we consider date of employee
        timesheet is in employee timezone
        """
        employee_obj = self.pool['hr.employee']

        tz = False
        if employee_id:
            employee = employee_obj.browse(cr, uid, employee_id, context=context)
            tz = employee.user_id.partner_id.tz

        if not date:
            date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        att_tz = timezone(tz or 'utc')

        attendance_dt = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        att_tz_dt = pytz.utc.localize(attendance_dt)
        att_tz_dt = att_tz_dt.astimezone(att_tz)
        # We take only the date omiting the hours as we compare with timesheet
        # date_from which is a date format thus using hours would lead to
        # be out of scope of timesheet
        att_tz_date_str = datetime.strftime(att_tz_dt, DEFAULT_SERVER_DATE_FORMAT)
        return att_tz_date_str

    def _get_current_sheet(self, cr, uid, employee_id, date=False, context=None):

        sheet_obj = self.pool['hr_timesheet_sheet.sheet']
        if not date:
            date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        att_tz_date_str = self._get_attendance_employee_tz(
                cr, uid, employee_id,
                date=date, context=context)
        sheet_ids = sheet_obj.search(cr, uid,
            [('date_from', '<=', att_tz_date_str),
             ('date_to', '>=', att_tz_date_str),
             ('employee_id', '=', employee_id)],
            limit=1, context=context)
        return sheet_ids and sheet_ids[0] or False

    def _sheet(self, cursor, user, ids, name, args, context=None):
        res = {}.fromkeys(ids, False)
        for attendance in self.browse(cursor, user, ids, context=context):
            res[attendance.id] = self._get_current_sheet(
                    cursor, user, attendance.employee_id.id, attendance.name,
                    context=context)
        return res

    _columns = {
        'sheet_id': fields.function(_sheet, string='Sheet',
            type='many2one', relation='hr_timesheet_sheet.sheet',
            store={
                      'hr_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                      'hr.attendance': (lambda self,cr,uid,ids,context=None: ids, ['employee_id', 'name', 'day'], 10),
                  },
            )
    }
    _defaults = {
        'name': _get_default_date,
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        sheet_id = context.get('sheet_id') or self._get_current_sheet(cr, uid, vals.get('employee_id'), vals.get('name'), context=context)
        if sheet_id:
            att_tz_date_str = self._get_attendance_employee_tz(
                    cr, uid, vals.get('employee_id'),
                   date=vals.get('name'), context=context)
            ts = self.pool.get('hr_timesheet_sheet.sheet').browse(cr, uid, sheet_id, context=context)
            if ts.state not in ('draft', 'new','confirm','done'):
                raise osv.except_osv(_('Error!'), _('You can not enter an attendance in a submitted timesheet. Ask your manager to reset it before adding attendance.'))
            elif ts.date_from > att_tz_date_str or ts.date_to < att_tz_date_str:
                raise osv.except_osv(_('User Error!'), _('You can not enter an attendance date outside the current timesheet dates.'))
        return super(hr_attendance,self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, *args, **kwargs):
        if isinstance(ids, (int, long)):
            ids = [ids]
        #self._check(cr, uid, ids)
        return super(hr_attendance,self).unlink(cr, uid, ids,*args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
       # self._check(cr, uid, ids)
        res = super(hr_attendance,self).write(cr, uid, ids, vals, context=context)
        if 'sheet_id' in context:
            for attendance in self.browse(cr, uid, ids, context=context):
                if context['sheet_id'] != attendance.sheet_id.id:
                    raise osv.except_osv(_('User Error!'), _('You cannot enter an attendance ' \
                            'date outside the current timesheet dates.'))
        return res

    def _check(self, cr, uid, ids):
        for att in self.browse(cr, uid, ids):
            if att.sheet_id and att.sheet_id.state not in ('draft', 'new'):
                raise osv.except_osv(_('Error!'), _('You cannot modify an entry in a confirmed timesheet'))
        return True


class hr_timesheet_sheet_sheet_day(osv.osv):
    _name = "hr_timesheet_sheet.sheet.day"
    _description = "Timesheets by Period"
    _auto = False
    _order='name'
    _columns = {
        'name': fields.date('Date', readonly=True),
        'sheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Sheet', readonly=True, select="1"),
        'total_timesheet': fields.float('Total Timesheet', readonly=True),
        'total_attendance': fields.float('Attendance', readonly=True),
        'total_difference': fields.float('Difference', readonly=True),
    }
    _depends = {
        'account.analytic.line': ['date', 'unit_amount'],
        'hr.analytic.timesheet': ['line_id', 'sheet_id'],
        'hr.attendance': ['action', 'name', 'sheet_id'],
    }

    def init(self, cr):
        cr.execute("""create or replace view hr_timesheet_sheet_sheet_day as
            SELECT
                id,
                name,
                sheet_id,
                total_timesheet,
                total_attendance,
                cast(round(cast(total_attendance - total_timesheet as Numeric),2) as Double Precision) AS total_difference
            FROM
                ((
                    SELECT
                        MAX(id) as id,
                        name,
                        sheet_id,
                        SUM(total_timesheet) as total_timesheet,
                        CASE WHEN SUM(total_attendance) < 0
                            THEN (SUM(total_attendance) +
                                CASE WHEN current_date <> name
                                    THEN 1440
                                    ELSE (EXTRACT(hour FROM current_time AT TIME ZONE 'UTC') * 60) + EXTRACT(minute FROM current_time AT TIME ZONE 'UTC')
                                END
                                )
                            ELSE SUM(total_attendance)
                        END /60  as total_attendance
                    FROM
                        ((
                            select
                                min(hrt.id) as id,
                                l.date::date as name,
                                s.id as sheet_id,
                                sum(l.unit_amount) as total_timesheet,
                                0.0 as total_attendance
                            from
                                hr_analytic_timesheet hrt
                                JOIN account_analytic_line l ON l.id = hrt.line_id
                                LEFT JOIN hr_timesheet_sheet_sheet s ON s.id = hrt.sheet_id
                            group by l.date::date, s.id
                        ) union (
                            select
                                -min(a.id) as id,
                                a.name::date as name,
                                s.id as sheet_id,
                                0.0 as total_timesheet,
                                SUM(((EXTRACT(hour FROM a.name) * 60) + EXTRACT(minute FROM a.name)) * (CASE WHEN a.action = 'sign_in' THEN -1 ELSE 1 END)) as total_attendance
                            from
                                hr_attendance a
                                LEFT JOIN hr_timesheet_sheet_sheet s
                                ON s.id = a.sheet_id
                            WHERE action in ('sign_in', 'sign_out')
                            group by a.name::date, s.id
                        )) AS foo
                        GROUP BY name, sheet_id
                )) AS bar""")



class hr_timesheet_sheet_sheet_account(osv.osv):
    _name = "hr_timesheet_sheet.sheet.account"
    _description = "Timesheets by Period"
    _auto = False
    _order='name'
    _columns = {
        'name': fields.many2one('account.analytic.account', 'Project / Analytic Account', readonly=True),
        'sheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Sheet', readonly=True),
        'total': fields.float('Total Time', digits=(16,2), readonly=True),
        'invoice_rate': fields.many2one('hr_timesheet_invoice.factor', 'Invoice rate', readonly=True),
        }

    _depends = {
        'account.analytic.line': ['account_id', 'date', 'to_invoice', 'unit_amount', 'user_id'],
        'hr.analytic.timesheet': ['line_id'],
        'hr_timesheet_sheet.sheet': ['date_from', 'date_to', 'user_id'],
    }

    def init(self, cr):
        cr.execute("""create or replace view hr_timesheet_sheet_sheet_account as (
            select
                min(hrt.id) as id,
                l.account_id as name,
                s.id as sheet_id,
                sum(l.unit_amount) as total,
                l.to_invoice as invoice_rate
            from
                hr_analytic_timesheet hrt
                left join (account_analytic_line l
                    LEFT JOIN hr_timesheet_sheet_sheet s
                        ON (s.date_to >= l.date
                            AND s.date_from <= l.date
                            AND s.user_id = l.user_id))
                    on (l.id = hrt.line_id)
            group by l.account_id, s.id, l.to_invoice
        )""")




class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'timesheet_range': fields.selection(
            [('day','Day'),('week','Week'),('month','Month')], 'Timesheet range',
            help="Periodicity on which you validate your timesheets."),
        'timesheet_max_difference': fields.float('Timesheet allowed difference(Hours)',
            help="Allowed difference in hours between the sign in/out and the timesheet " \
                 "computation for one sheet. Set this to 0 if you do not want any control."),
    }
    _defaults = {
        'timesheet_range': lambda *args: 'week',
        'timesheet_max_difference': lambda *args: 0.0
    }

class hr_employee(osv.osv):
    '''
    Employee
    '''

    _inherit = 'hr.employee'
    _description = 'Employee'

    def _timesheet_count(self, cr, uid, ids, field_name, arg, context=None):
        Sheet = self.pool['hr_timesheet_sheet.sheet']
        return {
            employee_id: Sheet.search_count(cr,uid, [('employee_id', '=', employee_id)], context=context)
            for employee_id in ids
        }

    _columns = {
        'timesheet_count': fields.function(_timesheet_count, type='integer', string='Timesheets'),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
