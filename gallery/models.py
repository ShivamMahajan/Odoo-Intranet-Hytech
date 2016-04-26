# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class gallery(osv.Model):
	_name = 'gallery.gallery'
	_columns={
		 # image: all image fields are base64 encoded and PIL-supported
		'image': fields.binary("Photo",
            help="This field holds the image used as photo for the employee, limited to 1024x1024px."),
    }




   
