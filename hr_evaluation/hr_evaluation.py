# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF


class hr_evaluation_plan(osv.Model):
    _name = "hr_evaluation.plan"
    _description = "Appraisal Plan"
    _columns = {
        'name': fields.char("Appraisal Plan", required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'phase_ids': fields.one2many('hr_evaluation.plan.phase', 'plan_id', 'Appraisal Phases', copy=True),
        'month_first': fields.integer('First Appraisal in (months)', help="This number of months will be used to schedule the first evaluation date of the employee when selecting an evaluation plan. "),
        'month_next': fields.integer('Periodicity of Appraisal (months)', help="The number of month that depicts the delay between each evaluation of this plan (after the first one)."),
        'active': fields.boolean('Active'),
       
        
    }
    _defaults = {
        'active': True,
        'month_first': 6,
        'month_next': 12,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
    }


class hr_evaluation_plan_phase(osv.Model):
    _name = "hr_evaluation.plan.phase"
    _description = "Appraisal Plan Phase"
    _order = "sequence"
    _columns = {
        'name': fields.char("Phase", size=64, required=True),
        'sequence': fields.integer("Sequence"),
        'company_id': fields.related('plan_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'plan_id': fields.many2one('hr_evaluation.plan', 'Appraisal Plan', ondelete='cascade'),
        'action': fields.selection([
            ('top-down', 'Top-Down Appraisal Requests'),
            ('bottom-up', 'Bottom-Up Appraisal Requests'),
            ('self', 'Self Appraisal Requests'),
            ('final', 'Final Interview')], 'Action', required=True),
        'survey_id': fields.many2one('survey.survey', 'Appraisal Form', required=True),
        'send_answer_manager': fields.boolean('All Answers',
            help="Send all answers to the manager"),
        'send_answer_employee': fields.boolean('All Answers',
            help="Send all answers to the employee"),
        'send_anonymous_manager': fields.boolean('Anonymous Summary',
            help="Send an anonymous summary to the manager"),
        'send_anonymous_employee': fields.boolean('Anonymous Summary',
            help="Send an anonymous summary to the employee"),
        'wait': fields.boolean('Wait Previous Phases',
            help="Check this box if you want to wait that all preceding phases " +
              "are finished before launching this phase."),
        'mail_feature': fields.boolean('Send mail for this phase', help="Check this box if you want to send mail to employees coming under this phase"),
        'mail_body': fields.text('Email'),
        'email_subject': fields.text('Subject'),
    }
    _defaults = {
        'sequence': 1,
        'is_plan_for_result':False,
        'mail_feature':True,
        'email_subject': _('''Regarding Appraisal '''),
        'mail_body': lambda *a: _('''
Date: %(date)s

Dear %(employee_name)s,

This is to inform you that your appraisal form has been created in ERP system %(eval_name)s.

Kindly submit your response.


Thanks,
--
%(user_signature)s

        '''),
    }


class hr_employee(osv.Model):
    _name = "hr.employee"
    _inherit="hr.employee"
    
    def _appraisal_count(self, cr, uid, ids, field_name, arg, context=None):
        Evaluation = self.pool['hr.evaluation.interview']
        return {
            employee_id: Evaluation.search_count(cr, uid, [('user_to_review_id', '=', employee_id)], context=context)
            for employee_id in ids
        }

    _columns = {
        'evaluation_plan_id': fields.many2one('hr_evaluation.plan', 'Appraisal Plan'),
        'evaluation_date': fields.date('Next Appraisal Date', help="The date of the next appraisal is computed by the appraisal plan's dates (first appraisal + periodicity)."),
        'appraisal_count': fields.function(_appraisal_count, type='integer', string='Appraisal Interviews'),
    }

    def lengthmonth(self,year, month):
        if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
            return 29
        return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

    def run_employee_evaluation(self, cr, uid, automatic=False, use_new_cursor=False, context=None):  # cronjob
        now = parser.parse(datetime.now().strftime('%Y-%m-%d'))
        obj_evaluation = self.pool.get('hr_evaluation.evaluation')
        users_obj = self.pool.get('res.users')
        ####Commented Out Appraisal create based on First month of Appraisal plan
        #emp_ids = self.search(cr, uid, [('evaluation_plan_id', '<>', False), ('evaluation_date', '=', False)], context=context)
        #for emp in self.browse(cr, uid, emp_ids, context=context):#######('evaluation_date', '<=', time.strftime("%Y-%m-%d"))
            #first_date = (now + relativedelta(months=emp.evaluation_plan_id.month_first)).strftime('%Y-%m-%d')
            #self.write(cr, uid, [emp.id], {'evaluation_date': first_date}, context=context)

        emp_ids = self.search(cr, uid, [('evaluation_plan_id', '<>', False)], context=context)
        for emp in self.browse(cr, uid, emp_ids, context=context):
            interview_boolean = False
            if emp.user_id.id != 1:
                employee_login_date_browse = users_obj.browse(cr, uid, [emp.user_id.id]).create_date
                diff_log_now = (now-datetime.strptime(employee_login_date_browse.split()[0], '%Y-%m-%d')).days
                if diff_log_now > 30:
                    today_year = now.year
                    today_month = now.month
                    days_of_month = self.lengthmonth(today_year, today_month)
                    next_date = date(today_year,today_month,days_of_month)
                    next_date_format = datetime.strptime(str(next_date) + " " + "00:00:00", '%Y-%m-%d %H:%M:%S')
                    self.write(cr, uid, [emp.id], {'evaluation_date': next_date}, context=context)
                    #if now == next_date_format:
                    plan_id = obj_evaluation.create(cr, uid, {'employee_id': emp.id, 'plan_id': emp.evaluation_plan_id.id,'manager':emp.parent_id.id,'company_id':emp.company_id.id}, context=context)
                    interview_boolean = obj_evaluation.button_plan_in_progress(cr, uid, [plan_id], context=context)
            ######################################### Creating Answer in new Survey for a Particular User ####################
            if interview_boolean:
                obj_evaluation_interview = self.pool.get('hr.evaluation.interview')
                obj_survey_user_input = self.pool.get('survey.user_input')
                obj_survey_user_input_line = self.pool.get('survey.user_input_line')
                obj_survey_question = self.pool.get('survey.question')
                obj_survey_label = self.pool.get('survey.label')
                interview_id_search = obj_evaluation_interview.search(cr,uid,[('evaluation_id','=',plan_id)])[0]
                interview_id_browse = obj_evaluation_interview.browse(cr,uid,interview_id_search)
                survey_user_id_browse = obj_survey_user_input.browse(cr,uid,[interview_id_browse.request_id.id])
                survey_question_search = obj_survey_question.search(cr,uid,[('survey_id','=',survey_user_id_browse.survey_id.id),('is_for_kit_cycle_1','=',True)])
                survey_question_browse = obj_survey_question.browse(cr,uid,survey_question_search)
                if survey_question_search :
                    survey_label_search = obj_survey_label.search(cr,uid,[('question_id_2','=',survey_question_search[0])])
                    count_interview = obj_evaluation_interview.search(cr, uid, [('user_id', '=', interview_id_browse.user_id.id)], context=context)
                    if len(count_interview) >1:
                        ids_previous = obj_survey_user_input_line.search(cr, uid, [('user_id','=',interview_id_browse.user_id.id),('previous_entry', '=', True)], context=context)
                        if len(ids_previous)!=0:
                            for record in range(0,len(ids_previous)):
                                line = obj_survey_user_input_line.browse(cr,uid,ids_previous[record])
                                vals={
                                    'user_input_id': survey_user_id_browse.id,
                                    'question_id': survey_question_search[0],
                                    'page_id': survey_question_browse.page_id.id,
                                    'survey_id': survey_question_browse.survey_id.id,
                                    'skipped': False,
                                    'answer_type': 'free_text', 
                                    'value_free_text': line.value_free_text,
                                    'value_suggested_row':survey_label_search[record],
                                    #'quizz_mark':'', 
                                    #'value_suggested': '',
                                    'user_id':interview_id_browse.user_id.id,
                                    'value_text':False,
                                    'is_appraisee':False,
                                    'is_appraiser':False,
                                    'is_kits1':True,
                                    'previous_entry':False,

                                }
                                obj_survey_user_input_line.create(cr,uid,vals)
                                obj_survey_user_input_line.write(cr,uid,[line.id],{'previous_entry':False})

                            ##########################################################################################
        return True
######################################ENd of Appraisal Cron ##########################



class hr_evaluation(osv.Model):
    _name = "hr_evaluation.evaluation"
    _inherit = "mail.thread"
    _description = "Employee Appraisal"

    ###############Get Cycle Type #######################
    def _get_default_cycle(self, cr, uid, context=None):
        today= datetime.now()
        cycle1 = ['April', 'May', 'June','July', 'August', 'September']
        if today.strftime('%B') in cycle1 :
            return 'cycle1'
        else:
            return 'cycle2'


    _columns = {
        'date': fields.date("Appraisee Deadline", required=True),
        'date_appraiser': fields.date("Appraiser Deadline", required=True),
        'employee_id': fields.many2one('hr.employee', "Employee", required=True),
        'note_summary': fields.text('Appraisal Summary'),
        'note_action': fields.text('Action Plan', help="If the evaluation does not meet the expectations, you can propose an action plan"),
        'rating': fields.selection([
            ('0', 'Significantly below expectations'),
            ('1', 'Do not meet expectations'),
            ('2', 'Meet expectations'),
            ('3', 'Exceeds expectations'),
            ('4', 'Significantly exceeds expectations'),
        ], "Appreciation", help="This is the appreciation on which the evaluation is summarized."),
        'survey_request_ids': fields.one2many('hr.evaluation.interview', 'evaluation_id', 'Appraisal Forms'),
        'plan_id': fields.many2one('hr_evaluation.plan', 'Plan', required=True),
        'state': fields.selection([
            ('draft', 'New'),
            ('cancel', 'Cancelled'),
            ('wait', 'Plan In Progress'),
            ('reviewed','Reviewed'),
            ('progress', 'Waiting Appreciation'),
            ('done', 'Done'),
        ], 'Status', required=True, readonly=True, copy=False),
        'date_close': fields.date('Ending Date', select=True),
        'cycle_type':fields.selection([('cycle1','Cycle 1'),('cycle2','Cycle 2')],"Cycle Type"),
        'manager': fields.many2one('hr.employee', 'Manager'),
        'company_id': fields.many2one('res.company', 'Company'),
        
        
    }
    _defaults = {
        'date': lambda *a: (parser.parse(datetime.now().strftime('%Y-%m-%d')) + timedelta(days=5)).strftime('%Y-%m-%d'),
        'date_appraiser': lambda *a: (parser.parse(datetime.now().strftime('%Y-%m-%d')) + timedelta(days=13)).strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'cycle_type':_get_default_cycle,

    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.browse(cr, uid, ids, context=context)
        res = []
        for record in reads:
            name = record.plan_id.name
            employee = record.employee_id.name_related
            res.append((record['id'], name + ' / ' + employee))
        return res

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        vals = {}
        vals['plan_id'] = False
        if employee_id:
            employee_obj = self.pool.get('hr.employee')
            for employee in employee_obj.browse(cr, uid, [employee_id], context=context):
                if employee and employee.evaluation_plan_id and employee.evaluation_plan_id.id:
                    vals.update({'plan_id': employee.evaluation_plan_id.id})
        return {'value': vals}

    def button_plan_in_progress(self, cr, uid, ids, context=None):
        hr_eval_inter_obj = self.pool.get('hr.evaluation.interview')
        if context is None:
            context = {}
        for evaluation in self.browse(cr, uid, ids, context=context):
            wait = False
            for phase in evaluation.plan_id.phase_ids:
                children = []
                if phase.action == "bottom-up":
                    children = evaluation.employee_id.child_ids
                elif phase.action in ("top-down", "final"):
                    if evaluation.employee_id.parent_id:
                        children = [evaluation.employee_id.parent_id]
                elif phase.action == "self":
                    children = [evaluation.employee_id]
                for child in children:
                    int_id = hr_eval_inter_obj.create(cr, uid, {
                        'evaluation_id': evaluation.id,
                        'phase_id': phase.id,
                        'deadline':evaluation.date,
                        # (parser.parse(datetime.now().strftime('%Y-%m-%d')) + relativedelta(months=+1,day=10)).strftime('%Y-%m-%d'),##months=+1,
                        'deadline_2':evaluation.date_appraiser,
                        'user_id': child.user_id.id,
                        'cycle_type':evaluation.cycle_type,
                        'manager':evaluation.manager.id,
                        'company_id':evaluation.company_id.id,
                    }, context=context)
                    if phase.wait:
                         wait = True
                    if not wait:
                        hr_eval_inter_obj.survey_req_waiting_answer(cr, uid, [int_id], context=context)
                    if (not wait) and phase.mail_feature:
                        body = phase.mail_body % {'employee_name': child.name, 'user_signature': child.user_id.signature,
                            'eval_name': phase.survey_id.title, 'date': time.strftime('%Y-%m-%d'), 'time': time}
                        sub = 'Regards Appraisal of %s' % child.name
                        if child.work_email:
                            vals = {'state': 'outgoing',
                                    'subject': sub,
                                    'body_html': '<pre>%s</pre>' % body,
                                    'email_to': child.work_email,
                                    'email_from': evaluation.employee_id.work_email}
                            self.pool.get('mail.mail').create(cr, uid, vals, context=context)

        self.write(cr, uid, ids, {'state': 'wait'}, context=context)
        return True

    def button_final_validation(self, cr, uid, ids, context=None):
        request_obj = self.pool.get('hr.evaluation.interview')
        self.write(cr, uid, ids, {'state': 'progress'}, context=context)
        for evaluation in self.browse(cr, uid, ids, context=context):
            if evaluation.employee_id and evaluation.employee_id.parent_id and evaluation.employee_id.parent_id.user_id:
                self.message_subscribe_users(cr, uid, [evaluation.id], user_ids=[evaluation.employee_id.parent_id.user_id.id], context=context)
            if len(evaluation.survey_request_ids) != len(request_obj.search(cr, uid, [('evaluation_id', '=', evaluation.id), ('state', 'in', ['done', 'cancel'])], context=context)):
                raise osv.except_osv(_('Warning!'), _("You cannot change state, because some appraisal forms have not been completed."))
        return True

    def button_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'date_close': time.strftime('%Y-%m-%d')}, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        interview_obj = self.pool.get('hr.evaluation.interview')
        evaluation = self.browse(cr, uid, ids[0], context)
        interview_obj.survey_req_cancel(cr, uid, [r.id for r in evaluation.survey_request_ids])
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def button_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('employee_id'):
            employee_id = self.pool.get('hr.employee').browse(cr, uid, vals.get('employee_id'), context=context)
            if employee_id.parent_id and employee_id.parent_id.user_id:
                vals['message_follower_ids'] = [(4, employee_id.parent_id.user_id.partner_id.id)]
        if 'date' in vals:
            new_vals = {'deadline': vals.get('date')}
            obj_hr_eval_iterview = self.pool.get('hr.evaluation.interview')
            for evaluation in self.browse(cr, uid, ids, context=context):
                for survey_req in evaluation.survey_request_ids:
                    obj_hr_eval_iterview.write(cr, uid, [survey_req.id], new_vals, context=context)
        return super(hr_evaluation, self).write(cr, uid, ids, vals, context=context)


class hr_evaluation_interview(osv.Model):
    _name = 'hr.evaluation.interview'
    _inherit = 'mail.thread'
    _rec_name = 'user_to_review_id'
    _description = 'Appraisal Interview'
    _columns = {
        'request_id': fields.many2one('survey.user_input', 'Survey Request', ondelete='cascade', readonly=True),
        'evaluation_id': fields.many2one('hr_evaluation.evaluation', 'Appraisal Plan', required=True),
        'phase_id': fields.many2one('hr_evaluation.plan.phase', 'Appraisal Phase', required=True),
        'user_to_review_id': fields.related('evaluation_id', 'employee_id', type="many2one", relation="hr.employee", string="Employee to evaluate"),
        'user_id': fields.many2one('res.users', 'Interviewer'),
        'state': fields.selection([('draft', "Draft"),
                                   ('waiting_answer', "In progress"),
                                   ('waiting_appraiser','Waiting For Review'),
                                   ('resend','Resend'),
                                   ('done', "Done"),
                                   ('cancel', "Cancelled")],
                                  string="State", required=True, copy=False),
        'survey_id': fields.related('phase_id', 'survey_id', string="Appraisal Form", type="many2one", relation="survey.survey"),
        'deadline': fields.related('request_id', 'deadline', type="datetime", string="Deadline"),
        'deadline_2':fields.related('request_id','deadline_2' ,type="datetime", string="Deadline2"),
        # 'reason_for_resend':fields.text('Reason for Resending'),
        'cycle_type':fields.selection([('cycle1','Cycle 1'),('cycle2','Cycle 2')],"Cycle Type"),
        'interview_year': fields.char("Appraisal Year"),
        'manager': fields.many2one('hr.employee', 'Manager'),
        'company_id': fields.many2one('res.company', 'Company'),

        
    }
    _defaults = {
        'state': 'draft',
        'interview_year': datetime.now().strftime('%Y'),

    }

    def create(self, cr, uid, vals, context=None):
        phase_obj = self.pool.get('hr_evaluation.plan.phase')
        survey_id = phase_obj.read(cr, uid, vals.get('phase_id'), fields=['survey_id'], context=context)['survey_id'][0]
        if vals.get('user_id'):
            user_obj = self.pool.get('res.users')
            partner_id = user_obj.read(cr, uid, vals.get('user_id'), fields=['partner_id'], context=context)['partner_id'][0]
        else:
            partner_id = None

        user_input_obj = self.pool.get('survey.user_input')
        if not vals.get('deadline'):
            vals['deadline'] = (parser.parse(datetime.now().strftime('%Y-%m-%d')) + relativedelta(months=+1,day=10)).strftime('%Y-%m-%d')
        ret = user_input_obj.create(cr, uid, {'survey_id': survey_id,
                                              'deadline': vals.get('deadline'),
                                              'deadline_2':vals.get('deadline_2'),
                                              'type': 'link',
                                              'partner_id': partner_id}, context=context)
        vals['request_id'] = ret
        return super(hr_evaluation_interview, self).create(cr, uid, vals, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.browse(cr, uid, ids, context=context)
        res = []
        for record in reads:
            name = record.survey_id.title
            res.append((record['id'], name))
        return res

    def survey_req_waiting_answer(self, cr, uid, ids, context=None):
        request_obj = self.pool.get('survey.user_input')
        for interview in self.browse(cr, uid, ids, context=context):
            if interview.request_id:
                request_obj.action_survey_resent(cr, uid, [interview.request_id.id], context=context)
            self.write(cr, uid, interview.id, {'state': 'waiting_answer'}, context=context)
        return True

    def survey_req_done(self, cr, uid, ids, context=None):
        for id in self.browse(cr, uid, ids, context=context):
            flag = False
            wating_id = 0
            if not id.evaluation_id.id:
                raise osv.except_osv(_('Warning!'), _("You cannot start evaluation without Appraisal."))
            records = id.evaluation_id.survey_request_ids
            for child in records:
                if child.state == "draft":
                    wating_id = child.id
                    continue
                if child.state != "done":
                    flag = True
            if not flag and wating_id:
                self.survey_req_waiting_answer(cr, uid, [wating_id], context=context)
        if not self.pool['res.users'].has_group(cr, uid, 'base.group_hr_project_manager'):
            raise osv.except_osv(_('Warning!'), _("You are not allowed to done appraisal Survey.Only your Reporting Manager can done this Survey."))
        else:
            self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

    def survey_req_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def action_print_survey(self, cr, uid, ids, context=None):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        context = dict(context or {})
        interview = self.browse(cr, uid, ids, context=context)[0]
        survey_obj = self.pool.get('survey.survey')
        response_obj = self.pool.get('survey.user_input')
        response = response_obj.browse(cr, uid, interview.request_id.id, context=context)
        context.update({'survey_token': response.token})
        return survey_obj.action_print_survey(cr, uid, [interview.survey_id.id], context=context)

    def action_start_survey(self, cr, uid, ids, context=None):
        context = dict(context or {})
        interview = self.browse(cr, uid, ids, context=context)[0]
        i=self.browse(cr, uid, ids, context=context)
        survey_obj = self.pool.get('survey.survey')
        response_obj = self.pool.get('survey.user_input')
        survey_pages_obj = self.pool.get('survey.page')
        survey_question_obj = self.pool.get('survey.question')
        survey_user_input_line_obj = self.pool.get('survey.user_input_line')
        # grab the token of the response and start appraisal
        response = response_obj.browse(cr, uid, interview.request_id.id, context=context)
        context.update({'survey_token': response.token})
        today = datetime.now() 

        if len(ids)==1:
            if uid == interview.evaluation_id.employee_id.user_id.id:
                survey_pages_search = survey_pages_obj.search(cr,uid,[('survey_id','=',response.survey_id.id)],context=context)
                survey_question_search = survey_question_obj.search(cr,uid,[('page_id','=',survey_pages_search[0])],context=context)
                vals = {
                    'user_input_id': interview.request_id.id,
                    'question_id': survey_question_search[0],
                    'page_id': survey_pages_search[0],
                    'survey_id': response.survey_id.id,
                    'skipped': False,
                    #'answer_type': 'free_text', 
                    #'value_free_text': interview.evaluation_id.employee_id,
                    #'value_suggested_row':survey_label_search[record],
                    #'quizz_mark':'', 
                    #'value_suggested': '',
                    #'user_id':interview_id_browse.user_id.id,
                    #'value_text':False,
                    #'is_appraisee':False,
                    #'is_appraiser':False,
                    #'is_kits1':True,
                   # 'previous_entry':False,
                }
                entries = survey_user_input_line_obj.search(cr,uid,[('create_date','>=',interview.create_date),('user_input_id','=',interview.request_id.id),('question_id','=',survey_question_search[0])])
                survey_question_browse = survey_question_obj.browse(cr,uid,[survey_question_search[0]],context=context)
                if survey_question_browse.type == "free_text":
                    vals.update({'answer_type':'free_text','value_free_text':interview.evaluation_id.employee_id.name})
                if survey_question_browse.type == "textbox":
                    vals.update({'answer_type':'text','value_text':interview.evaluation_id.employee_id.name})
                if len(entries)==0:
                    survey_user_input_line_obj.create(cr,uid,vals)


            if uid == interview.evaluation_id.employee_id.parent_id.user_id.id :##### changed this and response.write_uid.id != uid
                if interview.state == 'waiting_answer' or interview.state == 'resend':
                    interview_deadline = datetime.strptime(interview.deadline_2,"%Y-%m-%d %H:%M:%S")
                    if interview_deadline <  today:
                        raise osv.except_osv(_('Warning!'), _("Deadline For Filling this form is crossed. Please Contact Hr Officers. "))
                    else:
                        raise osv.except_osv(_('Warning!'), _("Please wait for your Subordinate to fill this Appraiser form.\n You get a email when your Subordinate finish his Appraisal form."))
                if interview.state == 'waiting_appraiser':
                    response_obj.write(cr, uid, [response.id],{'state':'new','last_displayed_page_id':''}, context=context)
        return survey_obj.action_start_survey(cr, uid, [interview.survey_id.id], context=context)

    # def action_resend_appraisal(self, cr, uid, ids, context=None):
    #     context = dict(context or {})
    #     interview = self.browse(cr, uid, ids, context=context)[0]
    #     response_obj = self.pool.get('survey.user_input')
    #     # grab the token of the response
    #     response = response_obj.browse(cr, uid, interview.request_id.id, context=context)
    #     if interview.reason_for_resend != False:
    #         response_obj.write(cr,uid,[response.id],{'state':'new','last_displayed_page_id':'','write_uid':interview.evaluation_id.employee_id.user_id.id},context=context)
    #         if interview.evaluation_id.employee_id.parent_id.work_email and interview.evaluation_id.employee_id.work_email:
    #             body =('''<p>This is to inform you that your Project Manager is not satisfy by your Appraisal Form submitted.\n <b>Below the Reasons Specified by your manager:</b> \n %s \n<b>In case any query contact your Project Manager </b> </p>''')%interview.reason_for_resend
    #             vals = {'state': 'outgoing',
    #                     'subject': 'Verification Needed on your Appraisal Form',
    #                     'body_html': '<pre>%s</pre>' % body,
    #                     'email_to': interview.evaluation_id.employee_id.work_email,
    #                     'email_from': interview.evaluation_id.employee_id.parent_id.work_email}
    #             self.pool.get('mail.mail').create(cr, uid, vals, context=context)
    #             self.write(cr,uid,[interview.id],{'state':'resend'})
    #     else:
    #         raise osv.except_osv(_('Warning!'), _("Please provide some Reasons before resending this form back to your suboridnate."))
    #     return True                                                   