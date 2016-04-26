import logging

import werkzeug.urls
import urlparse
import urllib2
import simplejson

import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time


from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF

_logger = logging.getLogger(__name__)

class res_users(osv.Model):
    _inherit = 'res.users'

    _columns = {
        'oauth_provider_id': fields.many2one('auth.oauth.provider', 'OAuth Provider'),
        'oauth_uid': fields.char('OAuth User ID', help="Oauth Provider user_id", copy=False),
        'oauth_access_token': fields.char('OAuth Access Token', readonly=True, copy=False),
    }

    _sql_constraints = [
        ('uniq_users_oauth_provider_oauth_uid', 'unique(oauth_provider_id, oauth_uid)', 'OAuth UID must be unique per provider'),
    ]

    def _auth_oauth_rpc(self, cr, uid, endpoint, access_token, context=None):
        params = werkzeug.url_encode({'access_token': access_token})
        if urlparse.urlparse(endpoint)[4]:
            url = endpoint + '&' + params
        else:
            url = endpoint + '?' + params
        f = urllib2.urlopen(url)
        response = f.read()
        return simplejson.loads(response)

    def _auth_oauth_validate(self, cr, uid, provider, access_token, context=None):
        """ return the validation data corresponding to the access token """
        p = self.pool.get('auth.oauth.provider').browse(cr, uid, provider, context=context)
        validation = self._auth_oauth_rpc(cr, uid, p.validation_endpoint, access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if p.data_endpoint:
            data = self._auth_oauth_rpc(cr, uid, p.data_endpoint, access_token)
            validation.update(data)
        return validation

    def _auth_oauth_signin(self, cr, uid, provider, validation, params, context=None):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: openerp.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        # company_obj = self.pool.get('res.company')
        company_obj=self.pool.get('employee_access.detail')
        try:
            oauth_uid = validation['user_id']
            user_ids = self.search(cr, uid, [("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
            if not user_ids:
                raise openerp.exceptions.AccessDenied()
            assert len(user_ids) == 1
            user = self.browse(cr, uid, user_ids[0], context=context)
            user.write({'oauth_access_token': params['access_token']})
            return user.login
        except openerp.exceptions.AccessDenied, access_denied_exception:
            if context and context.get('no_user_creation'):
                return None
            state = simplejson.loads(params['state'])
            token = state.get('t')
            oauth_uid = validation['user_id']
            email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))
            name = validation.get('name', email)
            email_client2 = email.split('@')
            ############ Validation For Email id in case of Multi Company
            # company_search = company_obj.search(cr,uid,[('email_domain','=',email_client2[1])],context=context)
            print ("email"),email
            company_search_domain = company_obj.search(cr,uid,[('email_login','=',email)],context=context)
            company_id=company_obj.browse(cr,uid,company_search_domain).company_id
            print ("company_id"),company_id.id
            company_search_obj=self.pool.get('res.company')
            company_search=company_search_obj.search(cr,uid,[('id','=',company_id.id)])
            print ("company_search"),company_search
            values = {
            
                'name': name,
                'login': email,
                'email': email,
                'oauth_provider_id': provider,
                'oauth_uid': oauth_uid,
                'oauth_access_token': params['access_token'],
                'active': True,
                'company_id':company_search[0],
                'company_ids':[(6, 0, [company_search[0]])],
                    
            }
            try:
                _, login, _ = self.signup(cr, uid, values, token, context=context)
                return login
            except SignupError:
                raise access_denied_exception


    def auth_oauth(self, cr, uid, provider, params, context=None):
        # Advice by Google (to avoid Confused Deputy Problem)
        # if validation.audience != OUR_CLIENT_ID:
        #   abort()
        # else:
        #   continue with the process
        access_token = params.get('access_token')
        validation = self._auth_oauth_validate(cr, uid, provider, access_token)
        # required check
        if not validation.get('user_id'):
            raise openerp.exceptions.AccessDenied()
        # retrieve and sign in user
        login = self._auth_oauth_signin(cr, uid, provider, validation, params, context=context)
        email_client1=login.split('@')
        # company_obj = self.pool.get('res.company')
        # company_search = company_obj.search(cr,uid,[('email_domain','=',email_client1[1])],context=context)
        company_obj=self.pool.get('employee_access.detail')
        company_search_domain = company_obj.search(cr,uid,[('email_login','=',login)],context=context)
        company_id=company_obj.browse(cr,uid,company_search_domain).company_id
        company_search=self.pool.get('res.company').search(cr,uid,[('id','=',company_id.id)])
        print ("company_search"),company_search
        if company_search:
            pass
        else:
            raise openerp.exceptions.AccessDenied()
        if not login:
            raise openerp.exceptions.AccessDenied()
        # return user credentials
        return (cr.dbname, login, access_token)

    def check_credentials(self, cr, uid, password):
        try:
            return super(res_users, self).check_credentials(cr, uid, password)
        except openerp.exceptions.AccessDenied:
            res = self.search(cr, SUPERUSER_ID, [('id', '=', uid), ('oauth_access_token', '=', password)])
            if not res:
                raise

class res_company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'email_domain': fields.char('Email Domain', required=True, help="Enter Company Email Domain",copy=False),
        'apply_leave_policy' :fields.boolean ("Apply Leave Policy",default=True),
        'employee_access':fields.one2many('employee_access.detail','company_id',string="Employee"),
    }


class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'use_for_timesheet': fields.boolean('Use for Timesheet', help="Check this if product is used for timesheet"),

    }


class employee_access_detail(osv.osv):
    _name="employee_access.detail"

    _columns={
        'company_id':fields.many2one('res.company',string="Company"),
        'email_login':fields.char("Email",required=True),
        'user_name':fields.char("Name",required=True),

    }
    
    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        sr_ids = self.search(cr, uid , [], context=context)
        lst = [x.email_login.lower() for x in self.browse(cr, uid, sr_ids, context=context) if x.email_login and x.id not in ids]
        for self_obj in self.browse(cr, uid, ids, context=context):
            if self_obj.email_login and self_obj.email_login.lower() in  lst:
                return False
            return True

    _sql_constraints = [('name_uniq', 'unique (email_login)', 'Email Id already exists !')]
    _constraints = [(_check_unique_insesitive, 'Email Id already exists !', ['email_login'])]

    def create(self,cr,uid,name,context=None):
        email_login_client=name['email_login'].split('@')
        company_obj = self.pool.get('res.company')
        email_domain_search = company_obj.search(cr,uid,[('id','=',name['company_id']),('email_domain','=',email_login_client[1])])
        if not email_domain_search:
            raise osv.except_osv(_('Warning!'), _("Email domain doesn\'t match with the company domain ! "))
        return super(employee_access_detail, self).create(cr, uid, name, context=None)

    def write(self,cr,uid,ids,name,context=None):
        
        if 'email_login' in name:
            company_id=self.browse(cr,uid,ids).company_id    
            email_login_client=name['email_login'].split('@')
            company_obj = self.pool.get('res.company')
            email_domain_search = company_obj.search(cr,uid,[('id','=',company_id.id),('email_domain','=',email_login_client[1])])
            if not email_domain_search:
                raise osv.except_osv(_('Warning!'), _("Email domain doesn\'t match with the company domain ! "))
        return super(employee_access_detail, self).write(cr, uid, ids,name, context=None)