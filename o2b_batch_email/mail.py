import base64
import logging
from email.utils import formataddr
from urlparse import urljoin

from openerp import api, tools
from openerp import SUPERUSER_ID
from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
from openerp.osv import fields, osv
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class mail_mail(osv.Model):
    _inherit = "mail.mail"

    def default_get(self, cr, uid, fields, context=None):
        # protection for `default_type` values leaking from menu action context (e.g. for invoices)
        # To remove when automatic context propagation is removed in web client
        if context and context.get('default_type') and context.get('default_type') not in self._all_columns['type'].column.selection:
            context = dict(context, default_type=None)
        return super(mail_mail, self).default_get(cr, uid, fields, context=context)

    def _get_partner_access_link(self, cr, uid, mail, partner=None, context=None):
        """Remove Email External links
        """
        return None

    def send_get_mail_to(self, cr, uid, mail, partner=None, context=None):
        """Forge the email_to with the following heuristic:
          - if 'partner', recipient specific (Partner Name <email>)
          - else fallback on mail.email_to splitting """
        if partner:
            email_to = [formataddr((partner.name, partner.email_send or partner.email))]
        else:
            email_to = tools.email_split(mail.email_to)
        return email_to

    def send_get_email_dict(self, cr, uid, mail, partner=None, context=None):
        """Return a dictionary for specific email values, depending on a
        partner, or generic to the whole recipients given by mail.email_to.

            :param browse_record mail: mail.mail browse_record
            :param browse_record partner: specific recipient partner
        """
        body = self.send_get_mail_body(cr, uid, mail, partner=partner, context=context)
        body_alternative = tools.html2plaintext(body)
        res = {
            'body': body,
            'body_alternative': body_alternative,
            'subject': self.send_get_mail_subject(cr, uid, mail, partner=partner, context=context),
            'email_to': self.send_get_mail_to(cr, uid, mail, partner=partner, context=context),
        }
        return res

