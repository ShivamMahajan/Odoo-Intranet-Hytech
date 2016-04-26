{
    'name': 'Unique Employee Dashboard',
    'version': '1.0',
    'category': 'Employee Dashboard',
    'description': """
This is to show employee specific Dashboard which include :
==============================================
   * Leave Analysis
   * Timesheet Analysis
   * Attendance Analysis Daily Basis
   * Attendance Analysis Based on Punching
""",
    'author': 'Deepak Nayak',
    'depends': ['board'],
    'data': [
        'employee_dashboard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
