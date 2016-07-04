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

class report_wizard(osv.osv_memory):
    _name='report.wizard'
     
    def _report_xls_work_user_report_fields(self, cr, uid, context=None):
        return [

                        'col1','col2','col3','col4',
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
            print"====================================",val.report_type
            if val.report_type=='My Report':
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

    def _code_get(self, cr, uid, context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        ids = report_obj.search(cr, uid, [('model','=','report.wizard')])
        res = report_obj.read(cr, uid, ids, ['name'], context)
        return [(r['name'], r['name']) for r in res]
    
    _columns={
            'report_type':fields.selection(_code_get, 'Report Type',  select=True, size=64, required=True), 
         }
