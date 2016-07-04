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

import html2text



_ir_translation_name = 'work.summary.xls'

class work_summary_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(work_summary_xls_parser, self).__init__(cr, uid, name, context=context)
        wiz_obj = self.pool.get('project.task.report.wizard')
        self.context = context
        wanted_list = wiz_obj._report_xls_work_summary_fields(cr, uid, context)
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


class work_summary_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(work_summary_xls, self).__init__(name, table, rml, parser, header, store)

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
                'header': [1, 24, 'text', _render("_('Project Name')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 24, 'text', _render("_('Assigned To')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('Task Name')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col4': {
                'header': [1, 15, 'text', _render("_('Planned Hours (Hrs.)')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col5': {
                'header': [1, 16, 'text', _render("_('Time Remaining (Hrs.)')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                 
            'col6': {
                'header': [1, 14, 'text', _render("_('Starting Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col7': {
                'header': [1, 14, 'text', _render("_('Deadline Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},         
            'col8': {
                'header': [1, 14, 'text', _render("_('Ending Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col9': {
                'header': [1, 12, 'text', _render("_('Stage')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                           
            'col10': {
                'header': [1, 24, 'text', _render("_('Work Summary')")],
                'lines': [1, 0, 'text',_render("work_summary or ''")],
                'totals': [1, 0, 'text', None]},
            'col11': {
                'header': [1, 14, 'text', _render("_('Task Date')")],
                'lines': [1, 0, 'text', _render("date")],
                'totals': [1, 0, 'text', None]},                                    
            'col12': {
                'header': [1, 15, 'text', _render("_('Time Spent (Hrs.)')")],
                'lines': [1,0, 'number', _render("time_spent")],
                'totals': [1, 0, 'text', None]},                                                     
            'col13': {
                'header': [1, 20, 'text', _render("_('Description')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                  
                                   
                  
        }
        self.col_specs_template1 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("project or ''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},   
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                  
            'col6': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col9': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                 
            'col10': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',_render("''")],
                'totals': [1, 0, 'text', None]},
            'col11': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col12': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                         
            'col13': {
                'header': [1, 20, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
                                                                                         
                                   
                  
        }

        self.col_specs_template2 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("done_by or ''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                   
            'col6': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},     
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col9': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                          
            'col10': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',_render("''")],
                'totals': [1, 0, 'text', None]},
            'col11': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col12': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                         
            'col13': {
                'header': [1, 20, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
                                   
                  
        }
        
        
        self.col_specs_template3 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("task or ''")],
                'totals': [1,0, 'text', None]},
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'number', _render("planned_hours")],
                'totals': [1, 0, 'text', None]},      
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'number', _render("remaining_hours")],
                'totals': [1, 0, 'text', None]},                 
            'col6': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("starting_date")],
                'totals': [1, 0, 'text', None]},       
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("deadline_date")],
                'totals': [1, 0, 'text', None]},  
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("ending_date")],
                'totals': [1, 0, 'text', None]},    
            'col9': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("stage or ''")],
                'totals': [1, 0, 'text', None]},                                                                                                                  
            'col10': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',_render("''")],
                'totals': [1, 0, 'text', None]},
            'col11': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col12': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col13': {
                'header': [1, 20, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("description")],
                'totals': [1, 0, 'text', None]},  
                                   
                  
        }

        self.col_specs_template4 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("from_date_print or ''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("from_date_print or ''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},      
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                 
            'col6': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},       
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},    
            'col9': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                  
            'col10': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',_render("''")],
                'totals': [1, 0, 'text', None]},
            'col11': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col12': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                        
            'col13': {
                'header': [1, 20, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
                                   
                  
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
        report_name = _("Project Status Report - Details")
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
        print"-------------*************",ws, row_pos, row_data,cell_style
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
        
        for line in objects:
            print"line===================",line,"object",objects
            
            task_work_ids = []
            task_ids = []
            list2 = []
            list3 = []
            list4 = []
            list5 = []
            project = ''
            work_summary = ''
            done_by = ''
            time_spent = 0.0
            date = ''
            task = ''
            deadline_date = ''
            planned_hours = 0.0
            remaining_hours = 0.0
            starting_date = ''
            ending_date = ''
            reviewer = ''
            description = ''
            stage = ''
            
            from_date = line.from_date
            till_date = line.till_date 
            till_datetime = datetime.strptime(till_date,"%Y-%m-%d")
            till_datetime = till_datetime.strftime("%Y-%m-%d 23:59:59") 

            from_date_format = datetime.strptime(from_date,"%Y-%m-%d")
            from_date_format = from_date_format.strftime("%d-%m-%Y")
            till_date_format = datetime.strptime(till_date,"%Y-%m-%d")
            till_date_format = till_date_format.strftime("%d-%m-%Y")

            from_date_print = 'From Date: ' + str(from_date_format)
            till_date_print = 'To Date: ' + str(till_date_format)

            c_specs = map(lambda x: self.render(x, self.col_specs_template4, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)              

            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
            ws.set_horz_split_pos(row_pos)

            if line.project_idss:
                for proj in line.project_idss:
                    
                    task_work_ids = []
                    task_ids = []
                    list2 = []
                    list3 = []
                    list4 = []
                    list5 = []
                    project = ''
                    work_summary = ''
                    done_by = ''
                    time_spent = 0.0
                    date = ''
                    task = ''
                    deadline_date = ''
                    planned_hours = 0.0
                    remaining_hours = 0.0
                    starting_date = ''
                    ending_date = ''
                    reviewer = ''
                    description = '' 
                    stage = '' 
                    cmp_date = ''                  
                    
                    task_work_ids = self.pool.get('project.task.work').search(self.cr,1,[('project_id','=',proj.id),('date','>=',from_date),('date','<=',till_datetime)], order='user_id,task_id,date')  
                    task_ids = self.pool.get('project.task').search(self.cr,1,[('project_id','=',proj.id),('date_deadline','<=',till_date),('stage_id','in',[28,11])], order='user_id,id,date_deadline')                    
                    project = proj.name or ''
                    
                    c_specs = map(lambda x: self.render(x, self.col_specs_template1, 'lines'), wanted_list)
                    row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)  
                    
                    if task_ids:
                        for tasks in task_ids:
                            val4 = self.pool.get('project.task').browse(self.cr, 1, tasks)
                            user1 = val4.user_id and val4.user_id.id or False
                            list5.append(user1)                                         
                    
                    if task_work_ids:
                        for task_work in task_work_ids:
                            val3 = self.pool.get('project.task.work').browse(self.cr, 1, task_work)
                            tw = val3.user_id and val3.user_id.id or False
                            task1 = val3.task_id and val3.task_id.id or False
                            list4.append(task1)
                            list3.append(tw)
                    total_task = list4 + task_ids 
                    if total_task:
                        total_task = list(set(total_task))          
                    total_user = list3 + list5
                    if total_user:
                        total_user = list(set(total_user))

                        for val1 in total_user:
                            val2 = self.pool.get('res.users').browse(self.cr, 1, val1)
                            done_by = val2.name or ''   

                            
                            c_specs = map(lambda x: self.render(x, self.col_specs_template2, 'lines'), wanted_list)
                            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                            
                            list2 = self.pool.get('project.task').search(self.cr, 1, [('id','in',total_task),('user_id','=',val1)])  
                            if list2:
                                for val_task in list2:
                                    val = self.pool.get('project.task').browse(self.cr, 1, val_task)   
                                    task = val.name or ''   
                                    planned_hours = val.planned_hours
                                    remaining_hours = val.remaining_hours
                                    description = val.description or ''
                                    
                                    starting_date = val.date_start or ''
                                    if starting_date=='':
                                        starting_date = '' 
                                    else:    
                                        starting_date = datetime.strptime(starting_date,"%Y-%m-%d %H:%M:%S")
                                        starting_date = starting_date.strftime("%d-%b-%Y")
                                    
                                    deadline_date = val.date_deadline or ''
                                    if deadline_date=='':
                                        deadline_date = ''
                                    else:
                                        deadline_date = datetime.strptime(deadline_date,"%Y-%m-%d")
                                        deadline_date = deadline_date.strftime("%d-%b-%Y")
                                    
                                    ending_date = val.date_end or ''
                                    if ending_date=='':
                                        ending_date = ''
                                    else:  
                                        ending_date = datetime.strptime(ending_date,"%Y-%m-%d %H:%M:%S")
                                        ending_date = ending_date.strftime("%d-%b-%Y")
                                    
                                    
                                    stage = val.stage_id and val.stage_id.name or ''
                                
                                    c_specs = map(lambda x: self.render(x, self.col_specs_template3, 'lines'), wanted_list)
                                    row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                                    
                                    if val.work_ids:
                                        for val6 in val.work_ids:
                           
                                            if val6.date>=from_date and val6.date<=till_datetime:
                                                work_summary = val6.name or ''
                                                time_spent = round(val6.hours,2) or 0.0
                                                
                                                date = val6.date or ''
                                                date = datetime.strptime(date,"%Y-%m-%d %H:%M:%S")
                                                date = date.strftime("%d-%b-%Y")
                                                    
                                                reviewer = val6.task_id and val6.task_id.reviewer_id and val6.task_id.reviewer_id.name or ''
                    
                                                c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
                                                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)        
                                      

work_summary_xls('report.work.summary.xls',
    'project.task.report.wizard',
    parser=work_summary_xls_parser)



_ir_translation_name = 'work.summary.report.xls'

class work_summary_report_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(work_summary_report_xls_parser, self).__init__(cr, uid, name, context=context)
        wiz_obj = self.pool.get('project.task.report.wizard')
        self.context = context
        wanted_list = wiz_obj._report_xls_work_summary_report_fields(cr, uid, context)
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


class work_summary_report_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(work_summary_report_xls, self).__init__(name, table, rml, parser, header, store)

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
                'header': [1, 30, 'text', _render("_('Employee Name')")],
                'lines': [1, 0, 'text', _render("user_name or ''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 30, 'text', _render("_('Estimated Effort (Hrs.)')")],
                'lines': [1,0, 'number', _render("planned_hrs_total")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('Time Spent (Hrs.)')")],
                'lines': [1, 0, 'number',  _render("time_spent_total")],
                'totals': [1,0, 'text', None]},                                                                                                                                  
                                   
                  
        }


        self.col_specs_template1 = {
                                   
            'col1': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("from_date_print or ''")],
                'totals': [1, 0, 'text', None]},    
            'col2': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("till_date_print or ''")],
                'totals': [1, 0, 'text', None]},                               
            'col3': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
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
        report_name = _("Employee Productivity Report - Summary")
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
        
        time_spent_total = 0.0
        planned_hrs_total = 0.0
        total_users = []
        task_work_ids = []
        task_list = []
        for line in objects:
            print"line===================",line,"object",objects

            from_date = line.from_date
            till_date = line.till_date 
            till_datetime = datetime.strptime(till_date,"%Y-%m-%d")
            till_datetime = till_datetime.strftime("%Y-%m-%d 23:59:59")

            from_date_format = datetime.strptime(from_date,"%Y-%m-%d")
            from_date_format = from_date_format.strftime("%d-%m-%Y")
            till_date_format = datetime.strptime(till_date,"%Y-%m-%d")
            till_date_format = till_date_format.strftime("%d-%m-%Y")

            from_date_print = 'From Date: ' + str(from_date_format)
            till_date_print = 'To Date: ' + str(till_date_format)

            c_specs = map(lambda x: self.render(x, self.col_specs_template1, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
            ws.set_horz_split_pos(row_pos)

            user = self.pool.get('res.users').browse(self.cr, 1, self.uid)
            company_id = user.company_id.id or False
            total_users = self.pool.get('res.users').search(self.cr,1,[('company_id','=',company_id)], order='name')
            if total_users:
                for val in self.pool.get('res.users').browse(self.cr, 1, total_users):
                    user_name = val.name or ''
                    time_spent_total = 0.0
                    planned_hrs_total = 0.0
                    task_list = []
                    task_work_ids = self.pool.get('project.task.work').search(self.cr,1,[('user_id','=',val.id),('date','>=',from_date),('date','<=',till_datetime)])
                    if task_work_ids:
                        for twork in self.pool.get('project.task.work').browse(self.cr, 1, task_work_ids):
                            time_spent_total = time_spent_total + twork.hours 

                            task_id=twork.task_id and twork.task_id.id or False
                            if task_id not in task_list:
                                task_list.append(task_id)
                                planned_hrs_total = planned_hrs_total + twork.task_id.planned_hours

                    planned_hrs_total = round(planned_hrs_total,2) or 0.0
                    time_spent_total = round(time_spent_total,2) or 0.0        

                    c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
                    row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)        
  

work_summary_report_xls('report.work.summary.report.xls',
    'project.task.report.wizard',
    parser=work_summary_report_xls_parser)





_ir_translation_name = 'project.status.report.summary.xls'

class project_status_report_summary_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(project_status_report_summary_xls_parser, self).__init__(cr, uid, name, context=context)
        wiz_obj = self.pool.get('project.task.report.wizard')
        self.context = context
        wanted_list = wiz_obj._report_xls_project_status_report_summary_fields(cr, uid, context)
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


class project_status_report_summary_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(project_status_report_summary_xls, self).__init__(name, table, rml, parser, header, store)

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
                'header': [1, 24, 'text', _render("_('Project Name')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                  
            'col2': {
                'header': [1, 24, 'text', _render("_('Task Name')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col3': {
                'header': [1, 12, 'text', _render("_('Stage')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                
            'col4': {
                'header': [1, 15, 'text', _render("_('Planned Hours (Hrs.)')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col5': {
                'header': [1, 16, 'text', _render("_('Time Remaining (Hrs.)')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col6': {
                'header': [1, 16, 'text', _render("_('Logged Hours (Hrs.)')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                
            'col7': {
                'header': [1, 14, 'text', _render("_('Starting Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col8': {
                'header': [1, 14, 'text', _render("_('Deadline Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},         
            'col9': {
                'header': [1, 14, 'text', _render("_('Ending Date')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                                
            'col10': {
                'header': [1, 30, 'text', _render("_('Description')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},   
            'col11': {
                'header': [1, 35, 'text', _render("_('Audit log Details')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                               
                                   
                  
        }
        self.col_specs_template1 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("project or ''")],
                'totals': [1, 0, 'text', None]},                                  
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col3': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},     
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},   
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col6': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                     
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col9': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                           
            'col10': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col11': {
                'header': [1, 35, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},    
                                                                                         
                                   
                  
        }
        
        self.col_specs_template2 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                  
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("''")],
                'totals': [1,0, 'text', None]},
            'col3': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col6': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},         
            'col9': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                                
            'col10': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},   
            'col11': {
                'header': [1, 35, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("msg_body or ''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                               
                                   
                  
        }        
        
        self.col_specs_template3 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                   
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("task or ''")],
                'totals': [1,0, 'text', None]},
            'col3': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("stage or ''")],
                'totals': [1, 0, 'text', None]},     
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'number', _render("planned_hours")],
                'totals': [1, 0, 'text', None]},      
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'number', _render("remaining_hours")],
                'totals': [1, 0, 'text', None]},    
            'col6': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'number', _render("logged_hours")],
                'totals': [1, 0, 'text', None]},                 
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("starting_date")],
                'totals': [1, 0, 'text', None]},       
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("deadline_date")],
                'totals': [1, 0, 'text', None]},  
            'col9': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("ending_date")],
                'totals': [1, 0, 'text', None]},                            
            'col10': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("description")],
                'totals': [1, 0, 'text', None]},  
            'col11': {
                'header': [1, 35, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
                                   
        } 

        self.col_specs_template4 = {
                                   
            'col1': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("from_date_print or ''")],
                'totals': [1, 0, 'text', None]},                                  
            'col2': {
                'header': [1, 24, 'text', _render("_('')")],
                'lines': [1, 0, 'text',  _render("till_date_print or ''")],
                'totals': [1,0, 'text', None]},
            'col3': {
                'header': [1, 12, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                
            'col4': {
                'header': [1, 15, 'text', _render("_('')")],
                'lines': [1,0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},  
            'col5': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]}, 
            'col6': {
                'header': [1, 16, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                
            'col7': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},
            'col8': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},         
            'col9': {
                'header': [1, 14, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                                
            'col10': {
                'header': [1, 30, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},   
            'col11': {
                'header': [1, 35, 'text', _render("_('')")],
                'lines': [1, 0, 'text', _render("''")],
                'totals': [1, 0, 'text', None]},                                                                                                                                               
                                   
                  
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
        report_name = _("Project Status Report - Summary")
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
        print"-------------*************",ws, row_pos, row_data,cell_style
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
    #    row_pos += 1
        row_pos = 1
        
        # Column headers
#         row_data = self.xls_row_template(c_specs, _("Grand Total"))
#         print"-------------*************",ws, row_pos, row_data,cell_style
#         row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
#         row_pos += 1
        # account move lines
        
        for line in objects:
            print"line===================",line,"object",objects
            
            task_work_ids = []
            task_ids = []
            list2 = []
            list3 = []
            list4 = []
            list5 = []
            project = ''
            work_summary = ''
            done_by = ''
            time_spent = 0.0
            date = ''
            task = ''
            deadline_date = ''
            planned_hours = 0.0
            remaining_hours = 0.0
            starting_date = ''
            ending_date = ''
            reviewer = ''
            description = ''
            stage = ''
            logged_hours = 0.0
            msg_body = ''
            
            from_date = line.from_date
            till_date = line.till_date 
            till_datetime = datetime.strptime(till_date,"%Y-%m-%d")
            till_datetime = till_datetime.strftime("%Y-%m-%d 23:59:59")   

            from_date_format = datetime.strptime(from_date,"%Y-%m-%d")
            from_date_format = from_date_format.strftime("%d-%m-%Y")
            till_date_format = datetime.strptime(till_date,"%Y-%m-%d")
            till_date_format = till_date_format.strftime("%d-%m-%Y")

            from_date_print = 'From Date: ' + str(from_date_format)
            till_date_print = 'To Date: ' + str(till_date_format)

            c_specs = map(lambda x: self.render(x, self.col_specs_template4, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)

            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
            ws.set_horz_split_pos(row_pos)

            if line.project_idss:
                for proj in line.project_idss:
                    
                    task_work_ids = []
                    task_ids = []
                    list2 = []
                    list4 = []
                    project = ''
                    work_summary = ''
                    done_by = ''
                    time_spent = 0.0
                    date = ''
                    task = ''
                    deadline_date = ''
                    planned_hours = 0.0
                    remaining_hours = 0.0
                    starting_date = ''
                    ending_date = ''
                    reviewer = ''
                    description = '' 
                    stage = '' 
                    cmp_date = '' 
                    logged_hours = 0.0  
                    msg_body = ''               
                    
                    task_work_ids = self.pool.get('project.task.work').search(self.cr,1,[('project_id','=',proj.id),('date','>=',from_date),('date','<=',till_datetime)], order='user_id,task_id,date')  
                    task_ids = self.pool.get('project.task').search(self.cr,1,[('project_id','=',proj.id),('date_deadline','<=',till_date),('stage_id','in',[28,11])], order='user_id,id,date_deadline')                    
                    project = proj.name or ''
                    
                    c_specs = map(lambda x: self.render(x, self.col_specs_template1, 'lines'), wanted_list)
                    row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)                                           
                    
                    if task_work_ids:
                        for task_work in task_work_ids:
                            val3 = self.pool.get('project.task.work').browse(self.cr, 1, task_work)
                            task1 = val3.task_id and val3.task_id.id or False
                            list4.append(task1)
                    total_task = list4 + task_ids 
                    if total_task:
                        total_task = list(set(total_task))          

                    list2 = self.pool.get('project.task').search(self.cr, 1, [('id','in',total_task)])  
                    if list2:
                        for val_task in list2:
                            logged_hours = 0.0
                            msg_body = ''

                            val = self.pool.get('project.task').browse(self.cr, 1, val_task)   
                            task = val.name or ''   
                            planned_hours = val.planned_hours
                            remaining_hours = val.remaining_hours
                            description = val.description or ''
                            
                            starting_date = val.date_start or ''
                            if starting_date=='':
                                starting_date = '' 
                            else:    
                                starting_date = datetime.strptime(starting_date,"%Y-%m-%d %H:%M:%S")
                                starting_date = starting_date.strftime("%d-%b-%Y")
                            
                            deadline_date = val.date_deadline or ''
                            if deadline_date=='':
                                deadline_date = ''
                            else:
                                deadline_date = datetime.strptime(deadline_date,"%Y-%m-%d")
                                deadline_date = deadline_date.strftime("%d-%b-%Y")
                            
                            ending_date = val.date_end or ''
                            if ending_date=='':
                                ending_date = ''
                            else:  
                                ending_date = datetime.strptime(ending_date,"%Y-%m-%d %H:%M:%S")
                                ending_date = ending_date.strftime("%d-%b-%Y")
                            
                            
                            stage = val.stage_id and val.stage_id.name or ''
                        
                            if val.work_ids:
                                for val6 in val.work_ids:
                   
                                    if val6.date>=from_date and val6.date<=till_datetime:
                                        logged_hours = logged_hours + val6.hours
                                        
                            logged_hours = round(logged_hours,2)

                            c_specs = map(lambda x: self.render(x, self.col_specs_template3, 'lines'), wanted_list)
                            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                            

                            if val.message_ids:
                                for msg in val.message_ids:
                                    msg = html2text.html2text(msg.body)
                                    msg1 = msg.encode('ascii','ignore')
                                    msg_body = str(msg1)
                                    msg_body = msg_body.strip()

                                    c_specs = map(lambda x: self.render(x, self.col_specs_template2, 'lines'), wanted_list)
                                    row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)
                                    


project_status_report_summary_xls('report.project.status.report.summary.xls',
    'project.task.report.wizard',
    parser=project_status_report_summary_xls_parser)