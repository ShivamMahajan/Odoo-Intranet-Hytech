# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 conexus (<http://conexus.at>).
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

{
    "name": "Time Attendance Terminal",
    "version": "1.0",
    "author": "conexus",
    "category": "Generic Modules/Human Resources",
    "website": "http://www.conexus.com",
    "description": """    Fetches SignIns/Outs from RFID Office Timer II Terminals via Scheduled Action or manually.
Sends the Employees RFID Key and Time to the Terminals.
HR Manager Role required for setting up the Terminals.

Office Timer II Terminals are available at:

    ADC-Elektronik GmbH
    Oestingsstrasse 13b
    59063 Hamm
    info@adc-elektronik.de
    +49 2381 91591-0

Please mention that you will use it with our OpenERP Module.
	
If setting the Standard Sign-In Sign-Out Time doesn't work, please ceck the License Number with ADC-Elektronik.
    """,
    'author': 'conexus',
    'website': 'http://www.openerp.com',
    'depends': ['resource', 'board', 'hr_attendance'],
    'init_xml': [],
    'update_xml': ['hr_attendance_terminal_view.xml', 'hr_attendance_terminal_action_rule.xml', 'security/ir.model.access.csv',
        ],
    'demo_xml': [

        ],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}

