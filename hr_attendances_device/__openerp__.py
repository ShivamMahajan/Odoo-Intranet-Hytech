{
	"name": "Attendance System Device Connection",
	"version": "1.0",
	"author":"Deepak Nayak",
	"category": "Human Resources",
	"website": "http://www.hytechpro.org",
	"description": ''' Fetches SignIns/Outs from ZkSoftware Device Integration
	''',
	"depends":['hr_attendance'],
	"data":[
		'security/ir_rule.xml',
        'security/ir.model.access.csv',
		'hr_attendance_device_views.xml',
		'hr_attendance_monthly_report.xml',
		'wizard/hr_attendance_monthly_summary_wizards_views.xml',
	],
	"installable": True,
	"auto_install": False,
	"application":True,
	
}
	
	
	