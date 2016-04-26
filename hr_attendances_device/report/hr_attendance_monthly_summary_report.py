import datetime
import time

import openerp
from openerp.osv import fields, osv
from openerp.report.interface import report_rml
from openerp.report.interface import toxml

from openerp.report import report_sxw
from openerp.tools import ustr
from openerp.tools.translate import _
from openerp.tools import to_xml

def lengthmonth(year, month):
    if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
        return 29
    return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

def strToDate(dt):
    if dt:
        dt_date=datetime.date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))
        return dt_date
    else:
        return


def emp_create_xml(self, cr, uid, dept, row_id, empid, name, som, eom):
    start_date = str(som).split()[0]
    end_date = str(eom).split()[0]
    difference_date = eom - som
    display={}
    if dept==0:
        count=0
        registry = openerp.registry(cr.dbname)
        attendance_ids = registry['hr_attendance.record.report'].search(cr, uid, [('employee_id','in',[empid,False]),('name','>=',start_date),('name','<=',end_date)],order='name ASC')
        ids_date_attendance = registry['hr_attendance.record.report'].read(cr, uid, attendance_ids, ['name','sign_in'])
        public_holidays = registry['company.public.holidays'].search(cr, uid, [('record_year','=',str(som.year))])
        employee_leaves =  registry['hr.holidays'].search(cr,uid,[('employee_id','in',[empid,False]), ('type', '=', 'remove')])
        ids_date_leaves = registry['hr.holidays'].read(cr, uid, employee_leaves, ['date_from','date_to','state'])

        for index in range(1,difference_date.days +2 ):
            diff=index-1
            current=som+datetime.timedelta(diff)
            display[index] = ''
            #### Checking Present
            for item in ids_date_attendance:
                if str(current).split()[0] == item['name']:
                    display[index]=5
                    count=count +1
                    if display[index] != '':
                        break
            ### Checking Public Holidays
            if display[index] == '':
                for pholiday in registry['company.public.holidays'].browse(cr,uid,public_holidays):
                    if pholiday.holiday_day == str(current).split()[0]:
                        display[index]=4
                        if display[index] != '':
                            break
            ### Checking Leave Request
            if display[index] == '':
                for item in ids_date_leaves:
                    date_from = datetime.datetime.strptime(item['date_from'].split()[0], '%Y-%m-%d')
                    date_to = datetime.datetime.strptime(item['date_to'].split()[0], '%Y-%m-%d')
                    current_update = current.strftime("%Y-%m-%d %H:%M:%S")
                    datetime_current = datetime.datetime.strptime(current_update.split()[0], '%Y-%m-%d')
                    if datetime_current >= date_from and datetime_current <= date_to:
                        display[index]= 1
                        if display[index] != '':
                            break

            ### Cheking Absent
            if display[index] == '':
                if current.strftime('%a') not in ['Sat','Sun']:
                    display[index] = 2
             
    data_xml=['<info id="%d" number="%d" val="%s" />' % (row_id,x,display[x]) for x in range(1,len(display)+1) ]
    
    # Computing the xml
    xml = '''
    %s
    <employee row="%d" id="%d" name="%s" sum="%s">
    </employee>
    ''' % (data_xml,row_id,dept, ustr(toxml(name)),count)

    return xml

class report_custom(report_rml):
    def create_xml(self, cr, uid, ids, data, context):
        registry = openerp.registry(cr.dbname)
        obj_emp = registry['hr.employee']
        depts=[]
        emp_id={}
        rpt_obj = registry['hr_attendance.record.report']
        rml_obj=report_sxw.rml_parse(cr, uid, rpt_obj._name,context)
        cr.execute("SELECT name FROM res_company")
        res=cr.fetchone()[0]
        date_xml=[]
        date_today=time.strftime('%Y-%m-%d %H:%M:%S')
        date_xml +=['<res name="%s" today="%s" />' % (to_xml(res),date_today)]
        legend = {'Present':'green','Weekends':'lightgrey','Absent':'red','Leave':'violet','Public Holiday':'blue'}
        today=datetime.datetime.today()
        today_year = today.strftime('%Y-%m-%d %H:%M:%S')[0:4]
        #### Check for Filter in Wizard to get Start and end date #####
        if data['form']['filter_by_date'] == True:
            first_date = datetime.datetime.strptime(data['form']['date_from'],'%Y-%m-%d') + datetime.timedelta()
            last_date =  datetime.datetime.strptime(data['form']['date_to'],'%Y-%m-%d') + datetime.timedelta()
        else :
            month_selected = data['form']['monthly_status']
            first_date = datetime.datetime(int(today_year),int(month_selected),1)
            number_of_days = lengthmonth( int(today_year), int(month_selected))
            last_date = datetime.datetime(int(today_year),int(month_selected),number_of_days)

        day_diff=last_date-first_date
 
        name = ''
        if len(data['form'].get('emp_id', ())) == 1:
            name = obj_emp.read(cr, uid, data['form']['emp_id'][0], ['name'])['name']

        date_xml.append('<from>%s</from>\n'% (str(rml_obj.formatLang(first_date.strftime("%Y-%m-%d"),date=True))))
        date_xml.append('<to>%s</to>\n' %(str(rml_obj.formatLang(last_date.strftime("%Y-%m-%d"),date=True))))
        date_xml.append('<name>%s</name>'%(name))

#        date_xml=[]
        for l in range(0,len(legend)):
            date_xml += ['<legend row="%d" id="%d" name="%s" color="%s" />' % (l+1, l+1, legend.keys()[l], legend.values()[l] )]
        date_xml += ['<date month="%s" year="%d" />' % (ustr(first_date.strftime('%B')),first_date.year),'<days>']

        cell=1
        if day_diff.days>=31:
            date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(first_date.replace(day=x).strftime('%a')), x-first_date.day+1) for x in range(first_date.day, day_diff.days +1)]
        else:
            #date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(first_date.replace(day=x).strftime('%a')), x-first_date.day+1) for x in range(first_date.day, last_date.day+1)]
            if day_diff.days>=(lengthmonth(first_date.year, first_date.month)-first_date.day):
                date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(first_date.replace(day=x).strftime('%a')),x-first_date.day+1) for x in range(first_date.day, lengthmonth(first_date.year, first_date.month)+1)]
            else:
                date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(first_date.replace(day=x).strftime('%a')), x-first_date.day+1) for x in range(first_date.day, last_date.day+1)]

        cell=x-first_date.day+1
        day_diff1=day_diff.days-cell+1


        width_dict={}
        month_dict={}

        i=1
        j=1
        year=first_date.year
        month=first_date.month
        month_dict[j]=first_date.strftime('%B')
        width_dict[j]=cell

        while day_diff1>0:
            if month + i <=12: # If month + i <=12
                if day_diff1 > lengthmonth(year,i+month): # Not on 30 else you have problems when entering 01-01-2009 for example
                    som1=datetime.date(year,month+i,1)
                    date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(som1.replace(day=x).strftime('%a')),cell+x) for x in range(1, lengthmonth(year,i+month)+1)]
                    i=i+1
                    j=j+1
                    month_dict[j]=som1.strftime('%B')
                    cell=cell+x
                    width_dict[j]=x

                else:
                    som1=datetime.date(year,month+i,1)
                    date_xml += ['<dayy number="%d" name="%s" cell="%d"/>' % (x, _(som1.replace(day=x).strftime('%a')),cell+x) for x in range(1, last_date.day +1 )]
                    i=i+1
                    j=j+1
                    month_dict[j]=som1.strftime('%B')
                    cell=cell+x
                    width_dict[j]=x

                day_diff1=day_diff1-x

        date_xml.append('</days>')
        date_xml.append('<cols>3.5cm%s,1.0cm</cols>\n' % (',0.7cm' * (day_diff.days+1)))
        date_xml = ''.join(date_xml)

        st='<cols_months>3.5cm'
        for m in range(1,len(width_dict)+1):
            st+=',' + str(0.7 *width_dict[m])+'cm'
        st+=',1.0cm</cols_months>\n'

        months_xml =['<months  number="%d" name="%s"/>' % (x, _(month_dict[x])) for x in range(1,len(month_dict)+1) ]
        months_xml.append(st)
        
        emp_xml=''
        row_id=1
        
        if data['model'] == 'hr.employee':
            for items in obj_emp.read(cr, uid, data['form']['emp_id'], ['id', 'name']):
                emp_xml += emp_create_xml(self, cr, uid, 0, row_id, items['id'], items['name'], first_date, last_date)
                row_id = row_id +1
                    
        header_xml = '''
        <header>
        <date>%s</date>
        <company>%s</company>
        </header>
        ''' % (str(rml_obj.formatLang(time.strftime("%Y-%m-%d"),date=True))+' ' + str(time.strftime("%H:%M")),to_xml(registry['res.users'].browse(cr,uid,uid).company_id.name))

        # Computing the xml
        xml='''<?xml version="1.0" encoding="UTF-8" ?>
        <report>
        %s
        %s
        %s
        %s
        </report>
        ''' % (header_xml,months_xml,date_xml, ustr(emp_xml))
        return xml

report_custom('report.hr_attendance.monthly.summary', 'hr_attendance.record.report', '', 'addons/hr_attendances_device/report/hr_attendance_monthly_summary.xsl')
