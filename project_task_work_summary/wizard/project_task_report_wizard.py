from openerp.osv import osv,fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import re
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools import flatten
import openerp.tools
import openerp.netsvc
import StringIO
import cStringIO
import base64
#import xlrd

class project_task_report_wizard(osv.osv_memory):
    _name='project.task.report.wizard'
     
    def _report_xls_work_summary_fields(self, cr, uid, context=None):
        return [

                        'col1','col2','col3','col4','col5','col6','col7','col8','col9','col10','col11','col12','col13',
        ]
    

    def _report_xls_work_summary_report_fields(self, cr, uid, context=None):
        return [

                        'col1','col2','col3',
        ]  


    def _report_xls_project_status_report_summary_fields(self, cr, uid, context=None):
        return [

                        'col1','col2','col3','col4','col5','col6','col7','col8','col9','col10','col11',
        ]          
    
    
    def _report_xls_template(self, cr, uid, context=None):
        """
        Template updates, e.g.

        my_change = {
            'move':{
                'header': [1, 20, 'text', _('My Move Title')],
                'lines': [1, 0, 'text', _render("line.move_id.name or ''")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}      
    
    
    def get_all_records(self,cr,uid,ids,context=None):
        res={}
        report_ids=[]
        
        for val in self.browse(cr,uid,ids):
            print"====================================",val.from_date,val.report_type
            if val.report_type=='Project Status Report - Details':
                report_obj = self.pool.get('ir.actions.report.xml')
                datas = {'ids' : ids}
                for rec in self.browse(cr,uid,ids):
                    report_name=rec.report_type                        
                    rpt_id =  report_obj.search(cr, uid, [('name','=',report_name)])[0]
                    if not rpt_id:
                        raise osv.except_osv(_('Invalid action !'), _('Report for This Name Does Not Exists.'))
                    rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])
                    break
                return {
                    'type' : 'ir.actions.report.xml',
                    'report_name':str(rpt_type['report_name']),
                    'datas' : datas,
                    'nodestroy':True,
                }

            if val.report_type=='Employee Productivity Report - Summary':
                report_obj = self.pool.get('ir.actions.report.xml')
                datas = {'ids' : ids}
                for rec in self.browse(cr,uid,ids):
                    report_name=rec.report_type                        
                    rpt_id =  report_obj.search(cr, uid, [('name','=',report_name)])[0]
                    if not rpt_id:
                        raise osv.except_osv(_('Invalid action !'), _('Report for This Name Does Not Exists.'))
                    rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])
                    break
                return {
                    'type' : 'ir.actions.report.xml',
                    'report_name':str(rpt_type['report_name']),
                    'datas' : datas,
                    'nodestroy':True,
                }   



            if val.report_type=='Project Status Report - Summary':
                report_obj = self.pool.get('ir.actions.report.xml')
                datas = {'ids' : ids}
                for rec in self.browse(cr,uid,ids):
                    report_name=rec.report_type                        
                    rpt_id =  report_obj.search(cr, uid, [('name','=',report_name)])[0]
                    if not rpt_id:
                        raise osv.except_osv(_('Invalid action !'), _('Report for This Name Does Not Exists.'))
                    rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])
                    break
                return {
                    'type' : 'ir.actions.report.xml',
                    'report_name':str(rpt_type['report_name']),
                    'datas' : datas,
                    'nodestroy':True,
                }                 


        return res       
     
     
    def _code_get(self, cr, uid, context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        ids = report_obj.search(cr, uid, [('model','=','project.task.report.wizard')])
        res = report_obj.read(cr, uid, ids, ['name'], context)
        return [(r['name'], r['name']) for r in res]
    
    _columns={
         'project_id':fields.many2one('project.project','Project'),
         'project_idss':fields.many2many('project.project','work_summ_project_rel','work_summ_wiz_id','project_id','Project'),
         'project_domain_idss':fields.many2many('project.project','work_summ_project_domain_rel','work_id1','mrp_workcenters_domain1','Project Domain'),
         'user_id':fields.many2one('res.users','Done By'),
         'from_date':fields.date('From Date', required=True),
         'till_date':fields.date('To Date', required=True),        
         'report_type':fields.selection(_code_get, 'Report Type',  select=True, size=64, required=True), 
              
         }


    def default_get(self, cr, uid, fields, context=None):
         
        if context is None: context = {}
        # no call to super!
        res={}
        proj_list = []
        proj_obj=self.pool.get('project.project')
        if uid==1:
            proj_list = proj_obj.search(cr, uid, [])           
        else:
            if self.pool['res.users'].has_group(cr, uid, 'project.group_project_sqa'):
                proj_list = proj_obj.search(cr, uid, [])
            else:    
                proj_list = proj_obj.search(cr, uid, [('user_id','=',uid)])    
            
            
        if proj_list:
            if 'project_domain_idss' in fields:
                res.update({'project_domain_idss':[(6,0,proj_list)]})
       
        return res
    
    
    
    
     
     
     