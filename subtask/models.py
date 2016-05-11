from openerp.osv import osv,fields

# class task_milestones(osv.osv):
# 	_name='task.milestone'

# 	_columns={
# 		'name':fields.char('Name',required=True),
# 		'milestone_id':fields.many2one('task.milestone','Parent'),
# 		'active':fields.boolean('Active',default=True),
# 	}
# class task_edit(osv.osv):
# 	_inherit="project.task"
# 	_columns={
# 		'parent_task_id':fields.many2one('project.task','Parent Task'),
# 		# 'active':fields.boolean('Active',default=True),
# 		# 'task_milestone_id':fields.many2one('task.milestone','Milestone',required=True),
# 	}
class _directory(osv.osv):
    # _name='project_task.combo'
    # _inherit = ['project.task','project.project']
    _inherit='project.task'
    _description = 'Project Directory'
    _order = 'name'
    _columns = {
        # 'name': fields.char('Name', required=True, select=1),

        'parent_task_id': fields.many2one('project.task', 'Parent Directory', select=1, change_default=True),
        'filter_id': fields.one2many('project.task', 'parent_task_id', 'Children'),
         
    }



