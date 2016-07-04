from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields,osv
from openerp import tools
from openerp.tools import amount_to_text_en
from openerp.report import report_sxw
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
import cStringIO
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf
import os
import base64, urllib
import openerp.netsvc
import xlwt
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate, _
from openerp import pooler
import re

_ir_translation_name = 'my.report.xls'

class report_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_xls_parser, self).__init__(cr, uid, name, context=context)
        wiz_obj = self.pool.get('report.wizard')
        self.context = context
        wanted_list = wiz_obj._report_xls_work_user_report_fields(cr, uid, context)
        template_changes = wiz_obj._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': template_changes,
            '_': self._,
        })
        

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) or src


class report_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(report_xls, self).__init__(name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(aml_cell_format + _xs['left'], num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(aml_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(rt_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)

        # XLS Template
        self.col_specs_template = {
                                   
            'col1': {
                'header': [1, 30, 'text', _render("_('Employee')")],
                'lines': [1, 0, 'text', _render("user_name or ''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 30, 'text', _render("_('Manager')")],
                'lines': [1,0, 'text', _render("employee_manager")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('Department')")],
                'lines': [1, 0, 'text',  _render("employee_department")],
                'totals': [1,0, 'text', None]},                                                                                                                                  
            'col4': {
                'header': [1, 24, 'text', _render("_('HTML')")],
                'lines': [1, 0, 'text',  _render("html")],
                'totals': [1,0, 'text', None]},         
                  
        }


      
    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        self.col_specs_template.update(_p.template_changes)
        _ = _p._

        wage_pos = 'wage' in wanted_list and wanted_list.index('wage')
        epf_deduction_pos = 'epf_deduction' in wanted_list and wanted_list.index('epf_deduction')
#         if not (credit_pos and debit_pos) and 'balance' in wanted_list:
#             raise oproject.task.report.wizardrm.except_orm(_('Customisation Error!'),
#                 _("The 'Balance' field is a calculated XLS field requiring the presence of the 'Debit' and 'Credit' fields !"))

        #report_name = objects[0]._description or objects[0]._name
        report_name = _("Employee Summary Report")
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
         ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
#        row_pos += 1
        row_pos = 1
        
        # Column headers
        # c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
        # row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        # row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
        # ws.set_horz_split_pos(row_pos)
#         row_data = self.xls_row_template(c_specs, _("Grand Total"))
#         print"-------------*************",ws, row_pos, row_data,cell_style
#         row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
#         row_pos += 1
        # account move lines
        
        # time_spent_total = 0.0
        # planned_hrs_total = 0.0
        # total_users = []
        # task_work_ids = []
        # task_list = []

        for line in objects:
            print"line===================",line,"object",objects

            # c_specs = map(lambda x: self.render(x, self.col_specs_template1, 'lines'), wanted_list)
            # row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            # row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
            ws.set_horz_split_pos(row_pos)

            # user = self.pool.get('res.users').browse(self.cr, 1, self.uid)
            # company_id = user.company_id.id or False
            # total_users = self.pool.get('res.users').search(self.cr,1,[('company_id','=',company_id)])
            # if total_users:
            #     for val in self.pool.get('res.users').browse(self.cr, 1, total_users):
            #         user_name = val.name or ''
            #         time_spent_total = 0.0
            #         planned_hrs_total = 0.0
            #         task_list = []
            #         task_work_ids = self.pool.get('project.task.work').search(self.cr,1,[('user_id','=',val.id),('date','>=',from_date),('date','<=',till_datetime)])
            #         if task_work_ids:
            #             for twork in self.pool.get('project.task.work').browse(self.cr, 1, task_work_ids):
            #                 time_spent_total = time_spent_total + twork.hours 

            #                 task_id=twork.task_id and twork.task_id.id or False
            #                 if task_id not in task_list:
            #                     task_list.append(task_id)
            #                     planned_hrs_total = planned_hrs_total + twork.task_id.planned_hours

            #         planned_hrs_total = planned_hrs_total or 0.0
            #         time_spent_total = time_spent_total or 0.0        
            
            user=self.pool.get('hr.employee')
            user_ids=user.search(self.cr,self.uid,[])
            for record in user.browse(self.cr,self.uid,user_ids):
                user_name=record.name
                employee_department=record.department_id.name
                employee_manager=record.parent_id.name
                html="""
                  **Initially Planned Hours**: 18.0  6.0

Stage changed

   **Ending Date**: 2016-06-13 08:01:05

   **Stage**: In-Progress  Completed

   **Deadline**: 2015-10-29  2016-06-09

Stage changed

   **Stage**: TODO  In-Progress

   **Starting Date**: 2015-10-28 14:21:24  2016-06-13 07:59:34

Stage changed

   **Stage**: Analysis  TODO

Task Assigned

   **Stage**: Analysis

   **Assigned to**: Abhimanyu Singh

   **Task Summary**: Swipe Implementation

   **Reviewer**: Abhimanyu Singh

   **Kanban State**: In Progress

   **Project**: Training Activities

Task created

   **Stage**: Analysis

   **Assigned to**: Abhimanyu Singh

   **Task Summary**: Swipe Implementation

   **Reviewer**: Abhimanyu Singh

   **Kanban State**: In Progress

   **Project**: Training Activities


LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL <type 'str'>
PPPPPPPPPPPPPPPPPP Stage changed

   **Ending Date**: 2016-06-21 06:10:04

   **Stage**: Completed

   **Deadline**: 2015-10-28  2016-06-10

Stage changed

   **Stage**: TODO  In-Progress

   **Starting Date**: 2015-10-28 14:19:02  2016-06-13 07:03:46

Stage changed

   **Stage**: Analysis  TODO

Task Assigned

   **Stage**: Analysis

   **Assigned to**: Bhanu Prakash

   **Task Summary**: google map

   **Reviewer**: Bhanu Prakash

   **Kanban State**: In Progress

   **Project**: Training Activities

Task created

   **Stage**: Analysis

   **Assigned to**: Bhanu Prakash

   **Task Summary**: google map

   **Reviewer**: Bhanu Prakash

   **Kanban State**: In Progress

   **Project**: Training Activities



                """
                html=html.strip()
                # html=re.sub('\s+',' ',html)
                c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)        
  
report_xls('report.my.report.xls','report.wizard',parser=report_xls_parser)