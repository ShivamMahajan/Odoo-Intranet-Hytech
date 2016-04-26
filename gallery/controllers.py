# -*- coding: utf-8 -*-
from openerp import http

# class Gallery(http.Controller):
#     @http.route('/gallery/gallery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gallery/gallery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gallery.listing', {
#             'root': '/gallery/gallery',
#             'objects': http.request.env['gallery.gallery'].search([]),
#         })

#     @http.route('/gallery/gallery/objects/<model("gallery.gallery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gallery.object', {
#             'object': obj
#         })