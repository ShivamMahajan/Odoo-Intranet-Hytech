# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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

import json
import logging
import werkzeug
import werkzeug.utils
from datetime import datetime
from math import ceil

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class WebsiteSurvey(http.Controller):

    ## HELPER METHODS ##

    def _check_bad_cases(self, cr, uid, request, survey_obj, survey, user_input_obj, context=None):
        # In case of bad survey, redirect to surveys list
        if survey_obj.exists(cr, SUPERUSER_ID, survey.id, context=context) == []:
            return werkzeug.utils.redirect("/survey/")

        # In case of auth required, block public user
        if survey.auth_required and uid == request.website.user_id.id:
            return request.website.render("survey.auth_required", {'survey': survey})

        # In case of non open surveys
        if survey.stage_id.closed:
            return request.website.render("survey.notopen")

        # If there is no pages
        if not survey.page_ids:
            return request.website.render("survey.nopages")

        # Everything seems to be ok
        return None

    def _check_deadline(self, cr, uid, user_input, context=None):
        '''Prevent opening of the survey if the deadline has turned out

        ! This will NOT disallow access to users who have already partially filled the survey !'''
        if user_input.deadline:
            dt_deadline = datetime.strptime(user_input.deadline, DTF)
            print ("Appraisee Deadline"),dt_deadline
            dt_deadline_2 = datetime.strptime(user_input.deadline_2, DTF)
            print ("Apprasier Deadline"),dt_deadline_2
            now = datetime.now().strftime("%Y-%m-%d")
            print ("Now is"),now
            dt_now = datetime.strptime(now, "%Y-%m-%d")
            print ("Today's Date"),dt_now
            hr_evaluation_interview_obj = request.registry['hr.evaluation.interview']
            hr_evaluation_interview_obj_search=hr_evaluation_interview_obj.search(cr,uid,[('request_id','=',user_input.id)])
            # The current Survey Record
            b=hr_evaluation_interview_obj.browse(cr,uid,hr_evaluation_interview_obj_search)
            user_to_review_id=b.user_to_review_id.user_id.id
            manager_id=b.manager.user_id.id
            if not request.registry['res.users'].has_group(cr, uid, 'base.group_hr_user')  :  # survey is not open anymore
                if uid==user_to_review_id :
                    if dt_now > dt_deadline:
                        return request.website.render("survey.notopen")
                if uid == manager_id:
                    if dt_now > dt_deadline_2:
                        return request.website.render("survey.notopen")

        return None

    ## ROUTES HANDLERS ##

    # Survey start
    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def start_survey(self, survey, token=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        survey_obj = request.registry['survey.survey']
        user_input_obj = request.registry['survey.user_input']

        # Test mode
        if token and token == "phantom":
            _logger.info("[survey] Phantom mode")
            user_input_id = user_input_obj.create(cr, uid, {'survey_id': survey.id, 'test_entry': True}, context=context)
            user_input = user_input_obj.browse(cr, uid, [user_input_id], context=context)[0]
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.website.render('survey.survey_init', data)
        # END Test mode

        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(cr, uid, request, survey_obj, survey, user_input_obj, context=context)
        if errpage:
            return errpage

        # Manual surveying
        if not token:
            vals = {'survey_id': survey.id}
            if request.website.user_id.id != uid:
                vals['partner_id'] = request.registry['res.users'].browse(cr, uid, uid, context=context).partner_id.id
            user_input_id = user_input_obj.create(cr, uid, vals, context=context)
            user_input = user_input_obj.browse(cr, uid, [user_input_id], context=context)[0]
        else:
            try:
                user_input_id = user_input_obj.search(cr, uid, [('token', '=', token)], context=context)[0]
            except IndexError:  # Invalid token
                return request.website.render("website.403")
            else:
                user_input = user_input_obj.browse(cr, uid, [user_input_id], context=context)[0]

        # Do not open expired survey
        errpage = self._check_deadline(cr, uid, user_input, context=context)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # Intro page
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.website.render('survey.survey_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey.id, user_input.token))

    # Survey displaying
    @http.route(['/survey/fill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:token>/<string:prev>'],
                type='http', auth='public', website=True)
    def fill_survey(self, survey, token, prev=None, **post):
        '''Display and validates a survey'''
        cr, uid, context = request.cr, request.uid, request.context
        survey_obj = request.registry['survey.survey']
        user_input_obj = request.registry['survey.user_input']
        hr_evaluation_interview = request.registry['hr.evaluation.interview']
        survey_questions_obj = request.registry['survey.question']
        user_input_line_obj = request.registry['survey.user_input_line']
        survey_page_obj = request.registry['survey.page']
        
        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(cr, uid, request, survey_obj, survey, user_input_obj, context=context)
        if errpage:
            return errpage

        # Load the user_input
        try:
            user_input_id = user_input_obj.search(cr, uid, [('token', '=', token)])[0]
        except IndexError:  # Invalid token
            return request.website.render("website.403")
        else:
            user_input = user_input_obj.browse(cr, uid, [user_input_id], context=context)[0]
        # Do not display expired survey (even if some pages have already been
        # displayed -- There's a time for everything!)
        errpage = self._check_deadline(cr, uid, user_input, context=context)
        if errpage:
            return errpage

        access_role = False
        access_role_by_questions = False
        questions_for_readonly = False
        question_count_for_kits = 0
        # Select the right page
        if user_input.state == 'new':  # First page
            page, page_nr, last = survey_obj.next_page(cr, uid, user_input, 0, go_back=False, context=context)
            if page:
                if survey.res_model =='hr_evaluation':
                    hr_evaluation_interview_search = hr_evaluation_interview.search(cr,uid,[('request_id','=',user_input.id)]) 
                    hr_evaluation_interview_browse = hr_evaluation_interview.browse(cr,uid,hr_evaluation_interview_search)
                    questions_ids = survey_questions_obj.search(cr, uid, [('page_id', '=', page.id),('type','in',['free_text','textbox','numerical_box','datetime','simple_choice','multiple_choice'])], context=context)
                    question_ids_kit = survey_questions_obj.search(cr,uid,[('page_id','=',page.id),('type','=','matrix_kits')])
                    if len(question_ids_kit) != 0:
                        input_lines = user_input_line_obj.search(cr,uid,[('question_id','=',question_ids_kit[0]),('user_input_id','=',user_input.id),('is_kits1','=',True),('user_id','=',hr_evaluation_interview_browse.user_id.id)])
                        if len(input_lines) != 0:
                            for lines in input_lines:
                                question_count_for_kits = question_count_for_kits + 1
                    questions = survey_questions_obj.browse(cr, uid, questions_ids, context=context)
                    for query in questions:
                        if query.is_for_appraiser == True:
                            access_role_by_questions = 'manager'

                    if uid == hr_evaluation_interview_browse.evaluation_id.employee_id.parent_id.user_id.id:
                        access_role = 'manager'
                    if uid == hr_evaluation_interview_browse.user_id.id:
                        access_role = 'employee'
            data = {'survey': survey, 'page': page, 'page_nr': page_nr, 'token': user_input.token,'group':access_role,'group_question':access_role_by_questions,'kits_nb':question_count_for_kits}
            if last:
                data.update({'last': True})
            return request.website.render('survey.survey', data)
        elif user_input.state == 'done':  # Display success message
            return request.website.render('survey.sfinished', {'survey': survey,
                                                               'token': token,
                                                               'user_input': user_input})


        elif user_input.state == 'skip':
            flag = (True if prev and prev == 'prev' else False)
            survey_page_browse = survey_page_obj.browse(cr, uid, [user_input.last_displayed_page_id.id],context=context)
            #############Save Button Logic############
            if survey_page_browse.is_for_monthly_appraisal_page == True:
                flag = True

            page, page_nr, last = survey_obj.next_page(cr, uid, user_input, user_input.last_displayed_page_id.id, go_back=flag, context=context)
            
            if page.is_for_monthly_appraisal_page == True:
                last = True
            ################################################
            if page:
                if survey.res_model =='hr_evaluation':
                    hr_evaluation_interview_search = hr_evaluation_interview.search(cr,uid,[('request_id','=',user_input.id)]) 
                    hr_evaluation_interview_browse = hr_evaluation_interview.browse(cr,uid,hr_evaluation_interview_search)
                    questions_ids = survey_questions_obj.search(cr, uid, [('page_id', '=', page.id),('type','in',['free_text','textbox','numerical_box','datetime','simple_choice','multiple_choice'])], context=context)
                    question_ids_kit = survey_questions_obj.search(cr,uid,[('page_id','=',page.id),('type','=','matrix_kits')])
                    if len(question_ids_kit) != 0:
                        input_lines = user_input_line_obj.search(cr,uid,[('question_id','=',question_ids_kit[0]),('user_input_id','=',user_input.id),('is_kits1','=',True),('user_id','=',hr_evaluation_interview_browse.user_id.id)])
                        if len(input_lines) != 0:
                            for lines in input_lines:
                                question_count_for_kits = question_count_for_kits + 1
                    questions = survey_questions_obj.browse(cr, uid, questions_ids, context=context)
                    for query in questions:
                        if query.is_for_appraiser == True:
                            access_role_by_questions = 'manager'

                    if uid == hr_evaluation_interview_browse.evaluation_id.employee_id.parent_id.user_id.id:
                        access_role = 'manager'
                    if uid == hr_evaluation_interview_browse.user_id.id:
                        access_role = 'employee'
            data = {'survey': survey, 'page': page, 'page_nr': page_nr, 'token': user_input.token,'group':access_role,'group_question':access_role_by_questions,'kits_nb':question_count_for_kits}
            if last:
                data.update({'last': True})
            return request.website.render('survey.survey', data)
        else:
            return request.website.render("website.403")

    # AJAX prefilling of a survey
    @http.route(['/survey/prefill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/prefill/<model("survey.survey"):survey>/<string:token>/<model("survey.page"):page>'],
                type='http', auth='public', website=True)
    def prefill(self, survey, token, page=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        user_input_line_obj = request.registry['survey.user_input_line']
        ret = {}
        # Fetch previous answers
        if page:
            ids = user_input_line_obj.search(cr, uid, [('user_input_id.token', '=', token), ('page_id', '=', page.id)], context=context)
        else:
            ids = user_input_line_obj.search(cr, uid, [('user_input_id.token', '=', token)], context=context)
        previous_answers = user_input_line_obj.browse(cr, uid, ids, context=context)
        # Return non empty answers in a JSON compatible format
        for answer in previous_answers:
            if not answer.skipped:
                answer_tag = '%s_%s_%s' % (answer.survey_id.id, answer.page_id.id, answer.question_id.id)
                answer_value = None
                if answer.answer_type == 'free_text' and not answer.value_suggested_row:
                    answer_value = answer.value_free_text
                elif answer.answer_type == 'text' and answer.question_id.type == 'textbox':
                    answer_value = answer.value_text
                elif answer.answer_type == 'text' and answer.value_suggested_row:
                    answer_tag = "%s_%s_%s" % (answer_tag, 'comment1',answer.value_suggested_row.id)
                    answer_value = answer.value_text

                elif answer.answer_type == 'free_text' and answer.value_suggested_row:
                    if answer.is_kits1 == True and answer.is_appraisee == False:
                        answer_tag = "%s_%s_%s" % (answer_tag, 'kits1',answer.value_suggested_row.id)
                        answer_value = answer.value_free_text
                    if answer.is_kits2 == True and answer.is_appraisee == False :
                        answer_tag = "%s_%s_%s" % (answer_tag, 'kits2',answer.value_suggested_row.id)
                        answer_value = answer.value_free_text
                    if answer.is_appraisee == True:
                        answer_tag = "%s_%s_%s" % (answer_tag, 'comment',answer.value_suggested_row.id)
                        answer_value = answer.value_free_text

                elif answer.answer_type == 'number' and not answer.value_suggested_row:
                    answer_value = answer.value_number.__str__()

                elif answer.answer_type == 'number' and answer.value_suggested_row:
                    answer_tag = "%s_%s" % (answer_tag, answer.value_suggested_row.id)
                    answer_value = answer.value_number.__str__()

                elif answer.answer_type == 'date':
                    answer_value = answer.value_date
                elif answer.answer_type == 'suggestion' and not answer.value_suggested_row:
                    answer_value = answer.value_suggested.id
                elif answer.answer_type == 'suggestion' and answer.value_suggested_row:
                    if answer.is_appraisee== True:
                        answer_tag = "%s_%s_%s" % (answer_tag, 'appraisee',answer.value_suggested_row.id)
                        answer_value = answer.value_suggested.id
                    if answer.is_appraiser== True:
                        answer_tag = "%s_%s_%s" % (answer_tag, 'appraiser',answer.value_suggested_row.id)
                        answer_value = answer.value_suggested.id
                    if answer.is_appraiser== False and answer.is_appraisee== False:
                        answer_tag = "%s_%s" % (answer_tag, answer.value_suggested_row.id)
                        answer_value = answer.value_suggested.id

                if answer_value:
                    dict_soft_update(ret, answer_tag, answer_value)
                else:
                    _logger.warning("[survey] No answer has been found for question %s marked as non skipped" % answer_tag)
        return json.dumps(ret)

    # AJAX scores loading for quiz correction mode
    @http.route(['/survey/scores/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def get_scores(self, survey, token, page=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        user_input_line_obj = request.registry['survey.user_input_line']
        ret = {}

        # Fetch answers
        ids = user_input_line_obj.search(cr, uid, [('user_input_id.token', '=', token)], context=context)
        previous_answers = user_input_line_obj.browse(cr, uid, ids, context=context)

        # Compute score for each question
        for answer in previous_answers:
            tmp_score = ret.get(answer.question_id.id, 0.0)
            ret.update({answer.question_id.id: tmp_score + answer.quizz_mark})
        return json.dumps(ret)

    # AJAX submission of a page
    @http.route(['/survey/submit/<model("survey.survey"):survey>'],
                type='http', methods=['POST'], auth='public', website=True)
    def submit(self, survey, **post):
        _logger.debug('Incoming data: %s', post)
        page_id = int(post['page_id'])
        cr, uid, context = request.cr, request.uid, request.context
        survey_obj = request.registry['survey.survey']
        questions_obj = request.registry['survey.question']
        questions_ids = questions_obj.search(cr, uid, [('page_id', '=', page_id)], context=context)
        questions = questions_obj.browse(cr, uid, questions_ids, context=context)

        # Answer validation
        errors = {}
        for question in questions:
            answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
            if question.constr_mandatory == True and not post['button_submit'] == 'save':
                errors.update(questions_obj.validate_question(cr, uid, question, post, answer_tag, context=context))

        ret = {}
        if (len(errors) != 0):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            # Store answers into database
            user_input_obj = request.registry['survey.user_input']

            user_input_line_obj = request.registry['survey.user_input_line']
            try:
                user_input_id = user_input_obj.search(cr, uid, [('token', '=', post['token'])], context=context)[0]
            except KeyError:  # Invalid token
                return request.website.render("website.403")
            for question in questions:
                answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
                user_input_line_obj.save_lines(cr, uid, user_input_id, question, post, answer_tag, context=context)

            user_input = user_input_obj.browse(cr, uid, user_input_id, context=context)
            go_back = post['button_submit'] == 'previous'
            next_page, _, last = survey_obj.next_page(cr, uid, user_input, page_id, go_back=go_back, context=context)
            vals = {'last_displayed_page_id': page_id}
            if next_page is None and not go_back and not post['button_submit'] == 'save':
                vals.update({'state': 'done'})
                if survey.res_model == 'hr_evaluation':
                    hr_evluation_obj = request.registry['hr.evaluation.interview'] 
                    hr_evluation_obj_parent = request.registry['hr_evaluation.evaluation']  
                    hr_evluation_id = hr_evluation_obj.search(cr,uid,[('request_id','=',user_input.id)])[0]
                    hr_evluation = hr_evluation_obj.browse(cr, uid, [hr_evluation_id], context=context)[0]
                    if user_input.id == hr_evluation.request_id.id:
                        if hr_evluation.evaluation_id.employee_id.work_email and uid == hr_evluation.evaluation_id.employee_id.user_id.id and user_input.write_uid.id == uid:
                            body_employee =('''<p>Dear %s</p>\n<p>This is to inform you that your subordinate %s  has filled the Appraisal Request.\nPlease review respective Appraisal Form and kindly provide your ratings against each Key Performance Areas.</p>''') % (hr_evluation.evaluation_id.employee_id.parent_id.name_related,hr_evluation.evaluation_id.employee_id.name_related)
                            vals_for_employee = {'state': 'outgoing',
                                    'subject': 'Regarding Apprasial of %s' % hr_evluation.evaluation_id.employee_id.name_related,
                                    'body_html': '<pre>%s</pre>' % body_employee,
                                    'email_to': hr_evluation.evaluation_id.employee_id.parent_id.work_email,
                                    'email_from': hr_evluation.evaluation_id.employee_id.work_email
                                }
                            request.registry['mail.mail'].create(cr, uid, vals_for_employee, context=context)
                            hr_evluation_obj.write(cr,uid,[hr_evluation.id],{'state':'waiting_appraiser'},context=context)
                        if hr_evluation.evaluation_id.employee_id.parent_id.work_email and uid == hr_evluation.evaluation_id.employee_id.parent_id.user_id.id and user_input.write_uid.id == uid:
                            body_manager =('''<p>Dear %s</p>\n<p>Your Appraisal Form has been successfully submitted by your Reporting Manager, %s for further HR processing.</p>''') % (hr_evluation.evaluation_id.employee_id.name_related,hr_evluation.evaluation_id.employee_id.parent_id.name_related)
                            vals_for_manager = {'state': 'outgoing',
                                    'subject': 'Regarding Apprasial of %s' % hr_evluation.evaluation_id.employee_id.name_related,
                                    'body_html': '<pre>%s</pre>' % body_manager,
                                    'email_to': hr_evluation.evaluation_id.employee_id.work_email ,
                                    'email_from': hr_evluation.evaluation_id.employee_id.parent_id.work_email
                                }
                            request.registry['mail.mail'].create(cr, uid, vals_for_manager, context=context)
                            hr_evluation_obj.write(cr,uid,[hr_evluation.id],{'state':'done'},context=context)
                            hr_evluation_obj_parent.write(cr,uid,[hr_evluation.evaluation_id.id],{'state':'reviewed'},context=context)
                        if request.registry['res.users'].has_group(cr, uid, 'base.group_hr_user') and uid != hr_evluation.evaluation_id.employee_id.user_id.id:
                            hr_evluation_obj.write(cr,uid,[hr_evluation.id],{'state':'done'},context=context)
                            hr_evluation_obj_parent.write(cr,uid,[hr_evluation.evaluation_id.id],{'state':'reviewed'},context=context)

            else:
                vals.update({'state': 'skip'})
            user_input_obj.write(cr, uid, user_input_id, vals, context=context)
            ret['redirect'] = '/survey/fill/%s/%s' % (survey.id, post['token'])
            if go_back:
                ret['redirect'] += '/prev'
            ###### Redirection for Save Button
            elif post['button_submit'] == 'save':
                ret['redirect'] = "/web#action=hr_evaluation.action_hr_evaluation_interview_tree"
        return json.dumps(ret)

    # Printing routes
    @http.route(['/survey/print/<model("survey.survey"):survey>',
                 '/survey/print/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def print_survey(self, survey, token=None, **post):
        '''Display an survey in printable view; if <token> is set, it will
        grab the answers of the user_input_id that has <token>.'''
        return request.website.render('survey.survey_print',
                                      {'survey': survey,
                                       'token': token,
                                       'page_nr': 0,
                                       'quizz_correction': True if survey.quizz_mode and token else False})

    @http.route(['/survey/results/<model("survey.survey"):survey>'],
                type='http', auth='user', website=True)
    def survey_reporting(self, survey, token=None, **post):
        '''Display survey Results & Statistics for given survey.'''
        result_template ='survey.result'
        current_filters = []
        filter_display_data = []
        filter_finish = False

        survey_obj = request.registry['survey.survey']
        if not survey.user_input_ids or not [input_id.id for input_id in survey.user_input_ids if input_id.state != 'new']:
            result_template = 'survey.no_result'
        if 'finished' in post:
            post.pop('finished')
            filter_finish = True
        if post or filter_finish:
            filter_data = self.get_filter_data(post)
            current_filters = survey_obj.filter_input_ids(request.cr, request.uid, survey, filter_data, filter_finish, context=request.context)
            filter_display_data = survey_obj.get_filter_display_data(request.cr, request.uid, filter_data, context=request.context)
        return request.website.render(result_template,
                                      {'survey': survey,
                                       'survey_dict': self.prepare_result_dict(survey, current_filters),
                                       'page_range': self.page_range,
                                       'current_filters': current_filters,
                                       'filter_display_data': filter_display_data,
                                       'filter_finish': filter_finish
                                       })
        # Quick retroengineering of what is injected into the template for now:
        # (TODO: flatten and simplify this)
        #
        #     survey: a browse record of the survey
        #     survey_dict: very messy dict containing all the info to display answers
        #         {'page_ids': [
        #
        #             ...
        #
        #                 {'page': browse record of the page,
        #                  'question_ids': [
        #
        #                     ...
        #
        #                     {'graph_data': data to be displayed on the graph
        #                      'input_summary': number of answered, skipped...
        #                      'prepare_result': {
        #                                         answers displayed in the tables
        #                                         }
        #                      'question': browse record of the question_ids
        #                     }
        #
        #                     ...
        #
        #                     ]
        #                 }
        #
        #             ...
        #
        #             ]
        #         }
        #
        #     page_range: pager helper function
        #     current_filters: a list of ids
        #     filter_display_data: [{'labels': ['a', 'b'], question_text} ...  ]
        #     filter_finish: boolean => only finished surveys or not
        #

    def prepare_result_dict(self,survey, current_filters=None):
        """Returns dictionary having values for rendering template"""
        current_filters = current_filters if current_filters else []
        survey_obj = request.registry['survey.survey']
        result = {'page_ids': []}
        for page in survey.page_ids:
            page_dict = {'page': page, 'question_ids': []}
            for question in page.question_ids:
                question_dict = {'question':question, 'input_summary':survey_obj.get_input_summary(request.cr, request.uid, question, current_filters, context=request.context), 'prepare_result':survey_obj.prepare_result(request.cr, request.uid, question, current_filters, context=request.context), 'graph_data': self.get_graph_data(question, current_filters)}
                page_dict['question_ids'].append(question_dict)
            result['page_ids'].append(page_dict)
        return result

    def get_filter_data(self, post):
        """Returns data used for filtering the result"""
        filters = []
        for ids in post:
            #if user add some random data in query URI, ignore it
            try:
                row_id, answer_id = ids.split(',')
                filters.append({'row_id': int(row_id), 'answer_id': int(answer_id)})
            except:
                return filters
        return filters

    def page_range(self, total_record, limit):
        '''Returns number of pages required for pagination'''
        total = ceil(total_record / float(limit))
        return range(1, int(total + 1))

    def get_graph_data(self, question, current_filters=None):
        '''Returns formatted data required by graph library on basis of filter'''
        # TODO refactor this terrible method and merge it with prepare_result_dict
        current_filters = current_filters if current_filters else []
        survey_obj = request.registry['survey.survey']
        result = []
        if question.type == 'multiple_choice':
            result.append({'key': str(question.question),
                           'values': survey_obj.prepare_result(request.cr, request.uid, question, current_filters, context=request.context)['answers']
                           })
        if question.type == 'simple_choice':
            result = survey_obj.prepare_result(request.cr, request.uid, question, current_filters, context=request.context)['answers']
        if question.type == 'matrix':
            data = survey_obj.prepare_result(request.cr, request.uid, question, current_filters, context=request.context)
            for answer in data['answers']:
                values = []
                for row in data['rows']:
                    values.append({'text': data['rows'].get(row), 'count': data['result'].get((row, answer))})
                result.append({'key': data['answers'].get(answer), 'values': values})
        return json.dumps(result)

def dict_soft_update(dictionary, key, value):
    ''' Insert the pair <key>: <value> into the <dictionary>. If <key> is
    already present, this function will append <value> to the list of
    existing data (instead of erasing it) '''
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary.update({key: [value]})
