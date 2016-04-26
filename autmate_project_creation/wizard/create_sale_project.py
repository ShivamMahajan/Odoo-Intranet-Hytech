from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class create_sale_project_inv(osv.osv_memory):
    _name = "create.sale.project.inv"
    _description = "Project creation after Sale Order line confirm"

    _columns = {
    	'use_existing':fields.boolean("Is Existing",help="Check this if u want to merge this with existing project"),
    	'name':fields.char("Project Name",required=True),
    	'project_id':fields.many2one('project.project','Existing Projects',required=True),
    	'user_id': fields.many2one('res.users', 'Project Manager', select=True, track_visibility='onchange'),
    	'partner_id': fields.many2one('res.partner', 'Customer'),
    	'pcr_id': fields.one2many('project.change.request', 'project_new_id', 'Change Request Lines', copy=True),
		'pd_id':fields.one2many('project.documents','project_new_id','Project Related Documents',copy=True),
    }

    _defaults = {
		'use_existing':False,
	}