# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields,osv

class hr_timesheet_report(osv.osv):
    _inherit = "hr.timesheet.report"
    _columns = {
        'to_invoice': fields.many2one('hr_timesheet_invoice.factor', 'Type of Invoicing',readonly=True),
        'nbr': fields.integer('# Nbr Timesheet',readonly=True),
        'total_diff': fields.float('# Total Diff',readonly=True),
        'total_timesheet': fields.float('# Total Timesheet',readonly=True),
        'total_attendance': fields.float('# Total Attendance',readonly=True),
        'department_id':fields.many2one('hr.department','Department',readonly=True),
        'date_from': fields.date('Date from',readonly=True,),
        'date_to': fields.date('Date to',readonly=True),
        'state' : fields.selection([
            ('new', 'New'),
            ('draft','Draft'),
            ('confirm','Confirmed'),
            ('done','Done')], 'Status', readonly=True),
        }

    

    def init(self, cr):
        # self._table = hr_timesheet_report
        select_str_parent = """
             SELECT min(hat.id) as id,
                    aal.date as date,
                    sum(aal.amount) as cost,
                    sum(aal.unit_amount) as quantity,
                    aal.account_id as account_id,
                    aal.journal_id as journal_id,
                    aal.product_id as product_id,
                    aal.general_account_id as general_account_id,
                    aal.user_id as user_id,
                    aal.company_id as company_id,
                    aal.currency_id as currency_id
        """
        select_str_child =  """,
                        htss.name,
                        htss.date_from,
                        htss.date_to,
                        count(*) as nbr,
                        ( SELECT sum(day.total_difference) AS sum
                            FROM hr_timesheet_sheet_sheet sheet
                            LEFT JOIN hr_timesheet_sheet_sheet_day day ON sheet.id = day.sheet_id
                            WHERE sheet.id = htss.id) AS total_diff,
                        ( SELECT sum(day.total_timesheet) AS sum
                            FROM hr_timesheet_sheet_sheet sheet
                            LEFT JOIN hr_timesheet_sheet_sheet_day day ON sheet.id = day.sheet_id
                            WHERE sheet.id = htss.id) AS total_timesheet,
                        ( SELECT sum(day.total_attendance) AS sum
                            FROM hr_timesheet_sheet_sheet sheet
                            LEFT JOIN hr_timesheet_sheet_sheet_day day ON sheet.id = day.sheet_id
                            WHERE sheet.id = htss.id) AS total_attendance,
                        aal.to_invoice,
                        htss.department_id,
                        htss.state"""


        from_str_parent = """
                account_analytic_line as aal
                    left join hr_analytic_timesheet as hat ON (hat.line_id=aal.id)
        """
        from_str_child = "left join hr_timesheet_sheet_sheet as htss ON (hat.sheet_id=htss.id)"

        group_by_str_parent = """
            GROUP BY aal.date,
                    aal.account_id,
                    aal.product_id,
                    aal.general_account_id,
                    aal.journal_id,
                    aal.user_id,
                    aal.company_id,
                    aal.currency_id
        """
        group_by_str_child = """,
                        htss.date_from,
                        htss.date_to,
                        aal.unit_amount,
                        aal.amount,
                        aal.to_invoice,
                        htss.name,
                        htss.state,
                        htss.id,
                        htss.department_id"""
        print ("Table name"),self._table
        #self._table = hr_timesheet_report

        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, select_str_parent+select_str_child , from_str_parent+from_str_child, group_by_str_parent+group_by_str_child))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
