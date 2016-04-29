# -*- coding: utf-8 -*-
from openerp.osv import osv ,fields

class subtask(osv.osv):
    # _name = 'subtask.subtask'
    _inherit='project.task'
    _columns={
		'task_name' :fields.many2one('project.task','Task'),
		'task_id':fields.one2many('project.task','task_name'),

	}
