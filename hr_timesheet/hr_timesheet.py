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
from datetime import *
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
import openerp
from openerp import SUPERUSER_ID

class hr_employee(osv.osv):
    _name = "hr.employee"
    _inherit = "hr.employee"
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', help="If you want to reinvoice working time of employees, link this employee to a service to determinate the cost price of the job."),
        'journal_id': fields.many2one('account.analytic.journal', 'Analytic Journal'),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string='Unit of Measure', store=True, readonly=True)
    }

    def _getAnalyticJournal(self, cr, uid, context=None):
        md = self.pool.get('ir.model.data')
        try:
            dummy, res_id = md.get_object_reference(cr, uid, 'hr_timesheet', 'analytic_journal')
            #search on id found in result to check if current user has read access right
            check_right = self.pool.get('account.analytic.journal').search(cr, uid, [('id', '=', res_id)], context=context)
            if check_right:
                return res_id
        except ValueError:
            pass
        return False

    def _getEmployeeProduct(self, cr, uid, context=None):
        md = self.pool.get('ir.model.data')
        try:
            dummy, res_id = md.get_object_reference(cr, uid, 'product', 'product_product_consultant')
            #search on id found in result to check if current user has read access right
            check_right = self.pool.get('product.template').search(cr, uid, [('id', '=', res_id)], context=context)
            if check_right:
                return res_id
        except ValueError:
            pass
        return False

    _defaults = {
        'journal_id': _getAnalyticJournal,
        'product_id': _getEmployeeProduct
    }


class hr_analytic_timesheet(osv.osv):
    _name = "hr.analytic.timesheet"
    _table = 'hr_analytic_timesheet'
    _description = "Timesheet Line"
    _inherits = {'account.analytic.line': 'line_id'}
    _order = "current_date_num asc, resources_name asc"

    _columns = {
        'line_id': fields.many2one('account.analytic.line', 'Analytic Line', ondelete='cascade', required=True),
        'partner_id': fields.related('account_id', 'partner_id', type='many2one', string='Partner', relation='res.partner', store=True),
        'current_date_num': fields.date('Record Date'),
        'current_month':fields.selection([('January', 'January'), ('February', 'February'), ('March','March'), ('April','April'),('May','May'), ('June','June'),('July','July'),('August','August'),('September','September'),('October','October'),('November','November'),('December','December')], 'Current Month', select=True),\
        'resources_name': fields.many2one('res.users', 'Resources'),
    }

    def unlink(self, cr, uid, ids, context=None):
        toremove = {}
        for obj in self.browse(cr, uid, ids, context=context):
            toremove[obj.line_id.id] = True
        super(hr_analytic_timesheet, self).unlink(cr, uid, ids, context=context)
        self.pool.get('account.analytic.line').unlink(cr, uid, toremove.keys(), context=context)
        return True


    def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount, company_id, unit=False, journal_id=False, context=None):
        res = {'value':{}}
        if prod_id and unit_amount:
            # find company
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.analytic.line', context=context)
            r = self.pool.get('account.analytic.line').on_change_unit_amount(cr, uid, id, prod_id, unit_amount, company_id, unit, journal_id, context=context)
            if r:
                res.update(r)
        # update unit of measurement
        if prod_id:
            uom = self.pool.get('product.product').browse(cr, uid, prod_id, context=context)
            if uom.uom_id:
                res['value'].update({'product_uom_id': uom.uom_id.id})
        else:
            res['value'].update({'product_uom_id': False})
        return res

    def _getEmployeeProduct(self, cr, uid, context=None):
        if context is None:
            context = {}
        emp_obj = self.pool.get('hr.employee')
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id') or uid)], context=context)
        if emp_id:
            emp = emp_obj.browse(cr, uid, emp_id[0], context=context)
            if emp.product_id:
                return emp.product_id.id
        return False

    def _getEmployeeUnit(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        if context is None:
            context = {}
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id') or uid)], context=context)
        if emp_id:
            emp = emp_obj.browse(cr, uid, emp_id[0], context=context)
            if emp.product_id:
                return emp.product_id.uom_id.id
        return False

    def _getGeneralAccount(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        if context is None:
            context = {}
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id') or uid)], context=context)
        if emp_id:
            emp = emp_obj.browse(cr, SUPERUSER_ID, emp_id[0], context=context)
            if bool(emp.product_id):
                a = emp.product_id.property_account_expense.id
                if not a:
                    a = emp.product_id.categ_id.property_account_expense_categ.id
                if a:
                    return a
        return False

    def _getAnalyticJournal(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        if context is None:
            context = {}
        if context.get('employee_id'):
            emp_id = [context.get('employee_id')]
        else:
            emp_id = emp_obj.search(cr, uid, [('user_id','=',context.get('user_id') or uid)], limit=1, context=context)
        if not emp_id:
            model, action_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'hr', 'open_view_employee_list_my')
            msg = _("Employee is not created for this user. Please create one from configuration panel.")
            raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
        emp = emp_obj.browse(cr, uid, emp_id[0], context=context)
        if emp.journal_id:
            return emp.journal_id.id
        else :
            raise osv.except_osv(_('Warning!'), _('No analytic journal defined for \'%s\'.\nYou should assign an analytic journal on the employee form.')%(emp.name))

    def _getAnalyticEmployeedefault(self,cr,uid,context=None):
        emp_obj = self.pool.get('hr.employee')
        emp_id = emp_obj.search(cr, uid, [('user_id','=',uid)], limit=1, context=context)
        emp_name_id = emp_obj.browse(cr,uid,emp_id)
        return emp_name_id.id


    _defaults = {
        'product_uom_id': _getEmployeeUnit,
        'product_id': _getEmployeeProduct,
        'general_account_id': _getGeneralAccount,
        'journal_id': _getAnalyticJournal,
        'date': lambda self, cr, uid, ctx: ctx.get('date', fields.date.context_today(self,cr,uid,context=ctx)),
        'user_id': lambda obj, cr, uid, ctx: ctx.get('user_id') or uid,
        'employee_analytic':_getAnalyticEmployeedefault,
    }
    def on_change_account_id(self, cr, uid, ids, account_id, context=None):
        return {'value':{}}

    def on_change_date(self, cr, uid, ids, date,context=None):
        project_obj = self.pool.get('project.project')
        analytic_obj = self.pool.get('account.analytic.account')
        employee_related_project = project_obj.search(cr,uid,['|',('members', '=', uid),('user_id','=',uid)],context=context)
        analytical_account_project = []
        for emp_project in project_obj.browse(cr,uid,employee_related_project,context):
            analytical_account_project.append(emp_project.analytic_account_id.id)
        if ids:
            new_date = self.read(cr, uid, ids[0], ['date'])['date']
            if date != new_date:
                warning = {'title':_('User Alert!'),'message':_('Changing the date will let this entry appear in the timesheet of the new date.')}
                return {'value':{},'warning':warning}
        return {'value':{'current_date_num':date},'domain':{'account_id':[('id','in',analytical_account_project)]}}

    def create(self, cr, uid, vals, context=None):
        #############--------Fetching members of Project------##############
        project_rel_obj = self.pool.get('project.project')
        if 'account_id' in vals :
            project_rel_analytic = project_rel_obj.search(cr,uid,[('analytic_account_id', '=', vals['account_id'])])
            project_browse = project_rel_obj.browse(cr,uid,project_rel_analytic)
            p_members = []
            for m in project_browse.members:
                p_members.append(m.id)
            vals.update({'members':[[6, False, p_members]]})
        ###################################################################################
        if context is None:
            context = {}
        emp_obj = self.pool.get('hr.employee')
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id') or uid)], context=context)
        ename = ''
        if emp_id:
            ename = emp_obj.browse(cr, uid, emp_id[0], context=context).name
        if not vals.get('journal_id',False):
           raise osv.except_osv(_('Warning!'), _('No \'Analytic Journal\' is defined for employee %s \nDefine an employee for the selected user and assign an \'Analytic Journal\'!')%(ename,))
        if not vals.get('account_id',False):
           raise osv.except_osv(_('Warning!'), _('No analytic account is defined on the project.\nPlease set one or we cannot automatically fill the timesheet.'))
    #############Added Logic For Filter By date###################
        current_month_date = datetime.strptime(vals['date'],"%Y-%m-%d")
        current_month_value = current_month_date.strftime("%B")
        vals.update({'current_date_num':vals['date'],'current_month':current_month_value,'resources_name':vals['user_id']})
        #####################
        return super(hr_analytic_timesheet, self).create(cr, uid, vals, context=context)

###################Cron Job For Fetching Date For Filter ############
    def fetch_date_for_timesheet(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        search_hr_records = self.search(cr,uid,['|','|',('current_date_num', '=', False),('current_month','=',False),('resources_name','=',False)], context=context)
        for activities_log in self.browse(cr, uid, search_hr_records, context=context):
            current_month_date = datetime.strptime(activities_log.date,"%Y-%m-%d")
            current_month_value = current_month_date.strftime("%B")
            self.write(cr,uid,[activities_log.id],{'current_date_num': activities_log.date,'current_month':current_month_value,'resources_name':activities_log.user_id.id}, context=context)
        return True
    

    def on_change_user_id(self, cr, uid, ids, user_id):
        if not user_id:
            return {}
        context = {'user_id': user_id}
        return {'value': {
            'product_id': self. _getEmployeeProduct(cr, uid, context),
            'product_uom_id': self._getEmployeeUnit(cr, uid, context),
            'general_account_id': self._getGeneralAccount(cr, uid, context),
            'journal_id': self._getAnalyticJournal(cr, uid, context),
        }}

class account_analytic_account(osv.osv):

    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'
    _columns = {
        'use_timesheets': fields.boolean('Timesheets', help="Check this field if this project manages timesheets"),
    }

    def on_change_template(self, cr, uid, ids, template_id, date_start=False, context=None):
        res = super(account_analytic_account, self).on_change_template(cr, uid, ids, template_id, date_start=date_start, context=context)
        if template_id and 'value' in res:
            template = self.browse(cr, uid, template_id, context=context)
            res['value']['use_timesheets'] = template.use_timesheets
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
