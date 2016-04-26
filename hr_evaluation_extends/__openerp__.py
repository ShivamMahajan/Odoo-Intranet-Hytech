{
    'name': 'Employee Appraisals Extends',
    'version': '1.0',
    'author': 'Deepak Nayak',
    'category': 'Human Resources',
    'sequence': 31,
    'website': 'https://www.hytechpro.org',
    'summary': 'Periodical Evaluations, Appraisals, Surveys',
    'depends': ['survey','hr'],
    'description': """
Periodical Employees evaluation and appraisals extends
========================================================

By using this application you can maintain the motivational process by doing periodical evaluations of your employees' performance. The regular assessment of human resources can benefit your people as well your organization.

An evaluation plan can be assigned to each employee. These plans define the frequency and the way you manage your periodic personal evaluations. You will be able to define steps and attach interview forms to each step.

Manages several types of evaluations: bottom-up, top-down, self-evaluations and the final evaluation by the manager.

Key Features
------------
* Ability to track Performance Rating based on different Parameter.
* Performance Rating can be track based on employee, different cycle, period and based on plan type.
""",
    "data": [
        'security/ir.model.access.csv',
        'security/hr_evaluation_extends_security.xml',
        'wizard/resend_reason_view.xml',
        'hr_evaluation_extends_view.xml',

        
    ],
    # 'test': [
    #     'test/test_hr_evaluation.yml',
    #     'test/hr_evalution_demo.yml',
    # ],
    'auto_install': False,
    'installable': True,
    'application': True,
}