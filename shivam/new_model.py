from openerp import models, fields,api

class Newmodel(models.Model):
	_name ='new.model'
	name = fields.Char("Country",required=True)
	parent_id = fields.Many2one('new.model',"Parent")

	@api.model
	def create(self,vals):
		print "Calling Create Method"
		print ("Env :"),self.env
		self.user_defined()
		print ("Recordset :"),self
		for record in self:
			print ("Records :"),record
			print record.name,record.parent_id
		return super(Newmodel,self).create(vals)
	
	# @api.onchange('parent_id')
	@api.model
	def user_defined(self):
		print ("User Defined Method")
		print ("Recordset :"),self
		# model_name=self.pool.get('new.model')
		# model_ids=model_name.search([])

		# for record in model_name.browse(model_ids):
		# 	print record
		# 	# print ("Records :"),record
		# 	# print record.name,record.parent_id
		# env = Environment(cr, uid, context) # cr, uid, context wrapped in env
		model = self.env['new.model']                  # retrieve an instance of MODEL
		recs = model.search([])         # search returns a recordset
		for rec in recs:                    # iterate over the records
		    print rec.name
		return None


