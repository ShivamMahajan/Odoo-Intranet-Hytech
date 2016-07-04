from openerp.osv import osv, fields
from openerp import SUPERUSER_ID ,api
from openerp.exceptions import Warning
from openerp.tools.translate import _




class add_skill_sets(osv.osv_memory):
    _name = "skillset.add.skillsets"

    def _get_employee_skills_set(self,cr,uid,context=None):
        employee_object=self.pool.get('hr.employee')
        employee_browse=employee_object.browse(cr,SUPERUSER_ID,context['active_id'])
        skill_set_ids = [skills.id for skills in employee_browse.key_skill ]
        return [(6,0,skill_set_ids)]

    _columns = {
    	'new_key_skill': fields.many2many('skillset.skillset','employee_skillset', 'keyskill_id', 'skill_rel', 'Key Skills'),
    	'user_id':fields.many2one('res.users','User ID'),
    }
    _defaults={
    	'user_id':lambda obj, cr, uid, context: uid,
        'new_key_skill':_get_employee_skills_set,
    }

    
    def add_key_skill(self,cr,uid,ids,context=None):
        employee_values={}
        employee_object=self.pool.get('hr.employee')
        employee_browse=employee_object.browse(cr,SUPERUSER_ID,context['active_id'])
        current_data=self.browse(cr,uid,ids)
        if current_data.user_id==employee_browse.user_id :
        	skill_set_ids = [skills.id for skills in current_data.new_key_skill ]
        	employee_values.update({'key_skill':[(6,0,skill_set_ids)]})
        	
        else:
        	raise Warning(_("You are only allowed to add your own skills ."))

        return  employee_object.write(cr,SUPERUSER_ID,context['active_id'],employee_values)


class crm_lead(osv.osv):

    _inherit='crm.lead'

    _columns={
     'currency_id': fields.many2one('res.currency', 'Currency', required=True),
    }
    	
    	

    	
