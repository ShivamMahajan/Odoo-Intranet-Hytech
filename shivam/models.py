from openerp.osv import osv,fields

class Shivam(osv.osv):
	def name_get(self, cr, uid, ids, context=None):
	    if not ids:
	        return []
	    reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
	    res = []
	    for record in reads:
	        name = record['name']
	        if record['parent_id']:
	            name = record['parent_id'][1]+' / '+name
	        res.append((record['id'], name))
	    return res

	def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
	    res = self.name_get(cr, uid, ids, context=context)
	    return dict(res)
	
	_name='shivam.mahajan'
	_columns={
	'name': fields.char("Technology", required=True),
	'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
	'parent_id': fields.many2one('shivam.mahajan', 'Parent Technology', select=True),


	}

	def create(self,cr,uid,vals,context=None):
		print "Calling Create Method"
		ids=super(Shivam,self).create(cr,uid,vals,context=None)
		self.user_defined_method(cr,uid,ids,context)
		return super(Shivam,self).create(cr,uid,vals,context=None)

	def write(self,cr,uid,ids,vals,context=None):
		print "Calling Write method"
		print super(Shivam,self).write(cr,uid,ids,vals,context=None)
		self.user_defined_method(cr,uid,ids,context=None)
		return super(Shivam,self).write(cr,uid,ids,vals,context=None)

	def unlink (self,cr,uid,ids,context=None):
		print "Calling Unlink Method "
		print super(Shivam,self).unlink (cr,uid,ids,context=None)
		self.user_defined_method(cr,uid,ids,context=None)
		return super(Shivam,self).unlink (cr,uid,ids,context=None)

	def user_defined_method(self,cr,uid,ids,context=None):
		print "Calling User user_defined_method"
		return None 