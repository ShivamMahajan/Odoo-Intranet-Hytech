# -*- coding: utf-8 -*-
from openerp import http

# class Subtask(http.Controller):
#     @http.route('/subtask/subtask/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/subtask/subtask/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('subtask.listing', {
#             'root': '/subtask/subtask',
#             'objects': http.request.env['subtask.subtask'].search([]),
#         })

#     @http.route('/subtask/subtask/objects/<model("subtask.subtask"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('subtask.object', {
#             'object': obj
#         })