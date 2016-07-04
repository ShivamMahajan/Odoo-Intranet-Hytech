from openerp.osv import osv,fields
class Project_Task_Work(osv.osv):
	_inherit='project.task.work'
	_columns={
		'project_id': fields.related('task_id', 'project_id', type='many2one', relation='project.project', string='Project', store=True, readonly=True),
		'manager_id': fields.related('task_id','project_id', 'analytic_account_id', 'user_id', type='many2one', relation='res.users', string='Project Manager',store=True, readonly=True),
		'date_start_task':fields.related('task_id','date_start',type='date',relation='project.task',string='Start Date',store=True,readonly=True),
		'date_deadline_task':fields.related('task_id','date_deadline',type='date',relation='project.task',string='Deadline',store=True,readonly=True),
		'task_stage':fields.related('task_id','stage_id',type='many2one',relation='project.task.type',string='Stage',readonly=True),
		'task_planned_hours':fields.related('task_id','planned_hours',type='float',relation='project.task',string='Planned Hours',store=True,readonly=True),
		'date_end_task':fields.related('task_id','date_end',type='date',relation='project.task',string='End Date',store=True,readonly=True),
	}
