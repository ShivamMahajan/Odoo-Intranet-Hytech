from openerp.addons.web.http import Controller, route, request
import base64


class DocumentViewerByUrl(Controller):

	#------------------------------------------------------
    # Document View  controllers
    #------------------------------------------------------
    @route(
        '/documents/<directory>/<tokenid>/<documentname>'
    , type='http', auth='user', website=True)
    def report_routes(self,directory, documentname,tokenid, **data):
        cr, uid, context = request.cr, request.uid, request.context
        attached_obj =request.registry['ir.attachment']
        attachment_doc_id = attached_obj.browse(cr,uid,[int(tokenid)])
        pdf_data = (attachment_doc_id.datas).decode('base64')
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf_data))]
        print ("Pdf htp headers"),pdfhttpheaders
        print ("Reponse is:"),request.make_response(pdf_data, headers=pdfhttpheaders)
        return request.make_response(pdf_data, headers=pdfhttpheaders)
       