# -*- coding: utf-8 -*-
from openerp import http

# class Shivam(http.Controller):
#     @http.route('/shivam/shivam/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/shivam/shivam/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('shivam.listing', {
#             'root': '/shivam/shivam',
#             'objects': http.request.env['shivam.shivam'].search([]),
#         })

#     @http.route('/shivam/shivam/objects/<model("shivam.shivam"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('shivam.object', {
#             'object': obj
#         })