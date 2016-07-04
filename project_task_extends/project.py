from openerp.osv import fields, osv
from datetime import datetime
class task(osv.osv):
    _inherit ='project.task'



    def _skin_change_colour(self, cr, uid,ids, field_name, arg,context=None):
        # model=self.pool.get('project.task')
        print "Calling Functional field"
        model_ids=self.search(cr,uid,[('user_id','=',uid)])
        for record in self.browse(cr,uid,model_ids):
            print record.user_id.name
            if record.date_deadline != False:
                date_deadline=datetime.strptime(record.date_deadline , '%Y-%m-%d')
                date_deadline=date_deadline.date()
                if record.stage_id.id==9 : # TO DO
                    if date_deadline==datetime.now().date(): 
                        record.color=3 #Yellow
                    elif date_deadline < datetime.now().date():
                        record.color=2 #Red
                    elif date_deadline > datetime.now().date():
                        record.color= 0 #White
                    else:
                        pass
                if record.stage_id.id== 10 : # In progress
                    if record.date_start != False :
                        date_start=datetime.strptime(record.date_start , '%Y-%m-%d %H:%M:%S')
                        date_start=date_start.date()
                        if date_deadline >= datetime.now().date() and date_deadline>=date_start:
                            record.color= 3 #Yellow
                        elif date_deadline< datetime.now().date():
                            record.color= 2 #Red
                        else:
                            pass
                if record.stage_id.id==11 : # Completed
                    if record.date_end != False :
                        date_end=datetime.strptime(record.date_end , '%Y-%m-%d %H:%M:%S')
                        date_end=date_end.date()
                        if date_deadline >= date_end and (record.remaining_hours) >=0:
                            record.color = 5 # Green
                        elif (record.remaining_hours ) < 0 and (record.remaining_hours)>=-2 and date_deadline >= date_end:
                            record.color=3 #Yellow
                        else:
                            record.color=2 # Red
        return None

    def task_skin_change_colour(self, cr, uid,context=None):
        print "Running Scheduler"
        model=self.pool.get('project.task')
        model_ids=model.search(cr,uid,[])
        for record in model.browse(cr,uid,model_ids):
            if record.date_deadline != False:
                date_deadline=datetime.strptime(record.date_deadline , '%Y-%m-%d')
                date_deadline=date_deadline.date()
                if record.stage_id.id==9 : # TO DO
                    if date_deadline==datetime.now().date(): 
                        record.color=3 #Yellow
                    elif date_deadline < datetime.now().date():
                        record.color=2 #Red
                    elif date_deadline > datetime.now().date():
                        record.color= 0 #White
                    else:
                        pass
                if record.stage_id.id== 10 : # In progress
                    if record.date_start != False :
                        date_start=datetime.strptime(record.date_start , '%Y-%m-%d %H:%M:%S')
                        date_start=date_start.date()
                        if date_deadline >= datetime.now().date() or date_deadline>=date_start:
                            record.color= 3 #Yellow
                        elif date_deadline< datetime.now().date():
                            record.color= 2 #Red
                        else:
                            pass
                if record.stage_id.id==11 : # Completed
                    if record.date_end != False :
                        date_end=datetime.strptime(record.date_end , '%Y-%m-%d %H:%M:%S')
                        date_end=date_end.date()
                        if date_deadline >= date_end and (record.remaining_hours) >=0:
                            record.color = 5 # Green
                            if record.planned_hours:
                                remaining_rate=(record.remaining_hours/record.planned_hours)*100
                                if remaining_rate>=30:
                                    record.priority='3' #Brilliant"
                                elif remaining_rate<30 and remaining_rate>=20:
                                    record.priority='2' #"Very Good"
                                elif remaining_rate<20 and remaining_rate>=10:
                                    record.priority='1' #"good"
                                else :
                                    record.priority='0' #"Nothing



                            # if record.remaining_hours>=2 :
                            #     if record.planned_hours<=18:
                            #         record.priority='3'
                            #     elif record.planned_hours <= 30 :
                            #         record.priority='2'
                            #     elif record.planned_hours > 30:
                            #         record.priority='1'
                            #     else:
                            #         vals['priority']='0'

                        elif (record.remaining_hours ) < 0 and (record.remaining_hours)>=-2 and date_deadline >= date_end:
                            record.color=3 #Yellow
                        else:
                            record.color=2 # Red
        return True


    _columns={
        'planned_hours': fields.float('Initially Planned Hours', required=True,track_visibility='onchange',help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
        'date_deadline': fields.date('Deadline', track_visibility='onchange',required=True,select=True, copy=False),
        'date_start': fields.datetime('Starting Date', select=True, copy=False,track_visibility='onchange'),
        'date_end': fields.datetime('Ending Date', select=True, copy=False ,track_visibility='onchange'),
        'colour_ids': fields.function(_skin_change_colour,type='boolean'),
        'priority': fields.selection([('0','Low'), ('1','Good'), ('2','Very Good'),('3','Brilliant')], 'Priority', select=True),
        'kanban_state': fields.selection([('normal', 'In Progress'),('blocked', 'Blocked'),('daily_activity', 'Daily Activity'),('done', 'Ready for next stage')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Normal is the default situation\n"
                                              " * Blocked indicates something is preventing the progress of this task\n"
                                              " * Ready for next stage indicates the task is ready to be pulled to the next stage\n"
                                              " * Daily Activity indicates task is completed on daily basis",
                                         required=False, copy=False),
        }

    def write(self,cr,uid,ids,vals,context=None):
        print "Calling Write method"
        if isinstance(ids, (int, long)):
            ids = [ids]
        # stage change: update date_last_stage_update*
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.datetime.now()
            if vals['stage_id']==10:
                vals['date_start'] = fields.datetime.now()
            if vals['stage_id']==11:
                vals['date_end'] = fields.datetime.now()
        # user_id change: update date_start
        if vals.get('user_id') and 'date_start' not in vals:
            vals['date_start'] = fields.datetime.now()
        record=self.browse(cr,uid,ids)
        if record:
            print record.user_id.name
            if record.date_deadline != False:
                date_deadline=datetime.strptime(record.date_deadline , '%Y-%m-%d')
                date_deadline=date_deadline.date()
                if record.stage_id.id==9 : # TO DO
                    if date_deadline==datetime.now().date(): 
                        vals['color']=3 #Yellow
                    elif date_deadline < datetime.now().date():
                        vals['color']=2 #Red
                    elif date_deadline > datetime.now().date():
                        vals['color']= 0 #White
                    else:
                        pass
                if record.stage_id.id== 10 : # In progress
                    if record.date_start != False :
                        date_start=datetime.strptime(record.date_start , '%Y-%m-%d %H:%M:%S')
                        date_start=date_start.date()
                        if date_deadline >= datetime.now().date() or date_deadline>=date_start:
                            vals['color']= 3 #Yellow
                        elif date_deadline< datetime.now().date():
                            vals['color']= 2 #Red
                        else:
                            pass
                if record.stage_id.id==11 : # Completed
                    if record.date_end != False :
                        date_end=datetime.strptime(record.date_end , '%Y-%m-%d %H:%M:%S')
                        date_end=date_end.date()
                        if date_deadline >= date_end and (record.remaining_hours) >=0:
                            vals['color'] = 5 # Green
                            if record.planned_hours:
                                remaining_rate=(record.remaining_hours/record.planned_hours)*100
                                if remaining_rate>=30:
                                    vals['priority']='3' #Brilliant"
                                elif remaining_rate<30 and remaining_rate>=20:
                                    vals['priority']='2' #"Very Good"
                                elif remaining_rate<20 and remaining_rate>=10:
                                    vals['priority']='1' #"good"
                                else :
                                    vals['priority']='0' #"Nothing"
                            # if record.remaining_hours>=2 :
                            #     if record.planned_hours<=18:
                            #         vals['priority']='3'
                            #     elif record.planned_hours <= 30 :
                            #         vals['priority']='2'
                            #     elif record.planned_hours > 30:
                            #         vals['priority']='1'
                            #     else:
                            #         vals['priority']='0'
                        elif (record.remaining_hours ) < 0 and (record.remaining_hours)>=-2 and date_deadline >= date_end:
                            vals['color']=3 #Yellow
                        else:
                            vals['color']=2 # Red
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the task changes.
        if vals and not 'kanban_state' in vals and 'stage_id' in vals:
            new_stage = vals.get('stage_id')
            vals_reset_kstate = dict(vals, kanban_state='normal')
            for t in self.browse(cr, uid, ids, context=context):
                write_vals = vals_reset_kstate if t.stage_id.id != new_stage else vals
                super(task, self).write(cr, uid, [t.id], write_vals, context=context)
            result = True
        else:
            result = super(task, self).write(cr, uid, ids, vals, context=context)
        if any(item in vals for item in ['stage_id', 'remaining_hours', 'user_id', 'kanban_state']):
            self._store_history(cr, uid, ids, context=context)
        return result
    