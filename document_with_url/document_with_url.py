from openerp.osv import fields, osv
from openerp import SUPERUSER_ID


class document_file(osv.osv):
	_inherit = 'ir.attachment'

	_columns = {
		'pdf_doc_url':fields.char('Converted URL', size=1024),
	}

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['parent_id'] = context.get('parent_id', False) or vals.get('parent_id', False)
		# take partner from uid
		if vals.get('res_id', False) and vals.get('res_model', False) and not vals.get('partner_id', False):
			vals['partner_id'] = self.__get_partner_id(cr, uid, vals['res_model'], vals['res_id'], context)

		if vals.get('datas', False):
			vals['file_type'], vals['index_content'] = self._index(cr, uid, vals['datas'].decode('base64'), vals.get('datas_fname', False), None)
		return super(document_file, self).create(cr, uid, vals, context)

	def write(self, cr, uid, ids, vals, context=None):
		if context is None:
			context = {}
		if vals.get('datas', False):
			vals['file_type'], vals['index_content'] = self._index(cr, uid, vals['datas'].decode('base64'), vals.get('datas_fname', False), None)
		return super(document_file, self).write(cr, uid, ids, vals, context)

	def generate_url_pdf_document(self, cr, uid,automatic=False, context=None):
		pdf_doc_ids = self.search(cr,uid,[('mimetype', '=', "application/pdf"),('type','=','binary'),('parent_id','<>',False),('pdf_doc_url','=',False)], context=context)
		irconfig_obj = self.pool['ir.config_parameter']
		document_obj = self.pool['document.directory']
		for pdf_doc_id in self.browse(cr, uid, pdf_doc_ids, context=context):
			if pdf_doc_id.datas_fname:
				url_list = []
				base_url = irconfig_obj.get_param(cr, SUPERUSER_ID, 'web.base.url')
				url_list.append(base_url)
				url_list.append('documents')
				document_id = document_obj.browse(cr,uid,[pdf_doc_id.parent_id.id])
				url_list.append(document_id.name)
				url_list.append(str(pdf_doc_id.id))
				url_list.append(pdf_doc_id.datas_fname)
				created_url = "/".join(url_list)
				self.write(cr,uid,[pdf_doc_id.id],{'pdf_doc_url': created_url}, context=context)

		return True