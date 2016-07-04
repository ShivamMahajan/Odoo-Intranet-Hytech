import base64
import datetime
import dateutil.relativedelta as relativedelta
import logging
import lxml
import urlparse
import openerp
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp import tools, api
from openerp.tools.translate import _
from urllib import urlencode, quote as quote
import base64
import logging
from email.utils import formataddr
from urlparse import urljoin


_logger = logging.getLogger(__name__)

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'email_send': fields.char('Email'),
    }

    def create(self, cr, uid, vals, context=None):
        if 'email' not in vals or not vals['email']:
            vals['email'] = '     '
        return super(res_partner, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        for partner in self.browse(cr, uid, ids):
            email = partner.email
            if 'email' in vals:
                if not vals['email']: vals['email'] = '       '
            if not email:
                vals['email'] = '  '
        return super(res_partner, self).write(cr, uid, ids, vals, context)


