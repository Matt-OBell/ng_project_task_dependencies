# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Mattobell (<http://www.mattobell.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp.osv import osv, fields
from tools.translate import _
import datetime

class project_task_depend(osv.Model):
    _name = "project.task.depend"

    _columns = {
        'code' : fields.char('Code', required=1),
        'name' : fields.char('Name', required=1)
    }

class project_project(osv.osv):
    _inherit = 'project.project'

    def _get_code(self, cr, uid, ids, context=None):
        res = self.pool.get("project.task.depend").search(cr, uid, [('code', '=', 'FTS')], context=context)
        return res and res[0] or False

    _columns = {
        'depend': fields.many2one("project.task.depend", 'Type of Dependencies', required=1,
                                  help='\nFinish to start (FS): A FS B = B can not start before A is finished. \
                                        \nFinish to finish (FF): A FF B = B can not finish before A is finished.\
                                       \nStart to start (SS): A SS B = B can not start before A starts. \
                                        \nStart to finish (SF): A SF B = B can not finish before A starts\
                                       \nNone: No dependancy\
                                        '),
    }

    _defaults = {
        'depend': _get_code
    }

class project_task(osv.Model):
    _inherit = "project.task"

    def _check_field_value(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj_task = self.browse(cr, uid, ids[0], context=context)
        lead_time = obj_task.lead_time or False
        lag_time = obj_task.lag_time or False
        if lag_time != 0.0 and lead_time != 0.0: 
            return False
        return True

    _columns = {
        'depend_type': fields.selection([('none', 'None'), ('fts','Finish To Start'), ('stf','Start To Finish'), ('sts','Start To Start'), ('ftf','Finish To Finish')], 'Type of Dependency', required=True ,
                                        help='\nFinish to start (FS): A FS B = B can not start before A is finished. \
                                        \nFinish to finish (FF): A FF B = B can not finish before A is finished.\
                                       \nStart to start (SS): A SS B = B can not start before A starts. \
                                        \nStart to finish (SF): A SF B = B can not finish before A starts\
                                       \nNone: No dependancy\
                                        '),
        'lead_time' : fields.float('Lead Time Hour(s)', required=1, help='Overlap between two tasks.'),
        'lag_time': fields.float('Lag Time Hour(s)', required=1, help='Gap between two tasks.'),
        'user_ids':fields.many2many('res.users', 'multi_emp_user_rel', 'task_id', 'u_id', 'Assign to Multiple Users'),
        'next_task_ids': fields.many2many('project.task', 'project_task_depend_rel', 'pv_task_id', 'nt_task_id', 'Next Tasks', states={'cancelled':[('readonly',True)]}),
        'previous_task_ids': fields.many2many('project.task', 'project_task_depend_rel', 'nt_task_id', 'pv_task_id', 'Previous Tasks', states={'cancelled':[('readonly',True)]}),
        
        
        'date_end': fields.datetime('Ending Date',select=True, required=1, help='End date of task. This will be used to calculate the dependancy rules if you are going to set on succeeding tasks.'),#override here.

    }
    _defaults = {
        'depend_type': 'fts'
    }
    
    def _check_task_depend(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj_task = self.browse(cr, uid, ids[0], context=context)
        previouse_task_ids = [p.id for p in obj_task.previous_task_ids]
        next_task_ids = [n.id for n in obj_task.next_task_ids]
        
        for p in previouse_task_ids:
            if p in next_task_ids:
                return False
        return True

    _constraints = [
        (_check_field_value, 'Error! You can not add lead time and lag time at same time on task.', ['lead_time', 'lag_time']),
        (_check_task_depend, 'Error! Same task cannot be Previous and at the same time Next to a given task.', ['next_task_ids', 'next_task_ids'])
    ]

    def onchange_project(self, cr, uid, id, project_id, context=None):
        res = super(project_task, self).onchange_project(cr, uid, id, project_id, context=context)
        if project_id:
            project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
            if project and project.depend:
                if project.depend.code == 'None':
                    d = 'none'
                if project.depend.code == 'FTS':
                    d = 'fts'
                if project.depend.code == 'STF':
                    d = 'stf'
                if project.depend.code == 'STS':
                    d = 'sts'
                if project.depend.code == 'FTF':
                    d = 'ftf'
                res['value']['depend_type'] = d
        return res

    def create(self, cr, uid, vals, context=None):
        res = super(project_task, self).create(cr, uid, vals, context)
        if vals.get('user_ids', False):
            #followers added for chatter 
            self.message_subscribe_users(cr, uid, [res], user_ids=vals['user_ids'][0][2], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # Start = open state and Finish = done state of Stage.
#        Basically Lead is overlap and Lag is delay.

        #Logic for adding followers and remove from followrs: *******************************************
        if vals.get('user_id', False):
            task_data = self.browse(cr, uid, ids, context=context)[0]
            old_users = [x.id for x in task_data.user_ids]
            if task_data.user_id:
                if vals.get('user_ids', False) and not task_data.user_id.id in vals['user_ids'][0][2]:
                    self.message_unsubscribe_users(cr, uid, ids, user_ids=[task_data.user_id.id], context=context)
                elif not vals.get('user_ids', False) and not task_data.user_id.id in old_users:
                    self.message_unsubscribe_users(cr, uid, ids, user_ids=[task_data.user_id.id], context=context)
        elif not vals.get('user_id', False):
            task_data = self.browse(cr, uid, ids, context=context)[0]
            old_users = [x.id for x in task_data.user_ids]
            if task_data.user_id:
                pass # no need of below code.. todo: remove it.
        if vals.get('user_ids', False):
            task_data = self.browse(cr, uid, ids, context=context)[0]
            old_users = [x.id for x in task_data.user_ids]
            for o in old_users:
                if not o in vals['user_ids'][0][2]:
                    self.message_unsubscribe_users(cr, uid, ids, user_ids=[o], context=context)
            #followers added for chatter 
            self.message_subscribe_users(cr, uid, ids, user_ids=vals['user_ids'][0][2], context=context)


        #Logic for dependancy*******************************************
        if vals.get('stage_id',False):
            task = self.browse(cr, uid, ids, context=context)[0]
            stage_my = self.pool.get('project.task.type').browse(cr, uid, [vals['stage_id']], context=context)[0]
            st_name = task.stage_id.name
            #send email to all users and followers
            body = "Task: %s\n\n \
                        Message: Stage of the task has been changed from %s to %s."%(task.name, st_name, stage_my.name)
            self.message_post(cr, uid, [ids[0]], body=body, subject=task.name+' (Stage Changed)', type='email',context=context)


            #if task has type of dependencies...
            if task.depend_type !='none' and task.previous_task_ids:
                #if Finish to Start doesn't have lead or lag time it check only state
                if task.depend_type == 'fts' and task.lead_time == 0.0 and task.lag_time == 0.0: #Finish to Start
                    for prev in task.previous_task_ids:
                        if prev.stage_id.state != 'done' and stage_my.state in ['open','done']:
                            raise osv.except_osv(_('Warning!'), _('You can not start this task since previous task(s) is still not done.'))
                #if Finish to Start have only lag_time then it will wait for start upto lag time after completed previous task . 
                elif task.depend_type == 'fts' and task.lead_time == 0.0 and task.lag_time > 0.0:
                    for prev in task.previous_task_ids:
                        end_date = datetime.datetime.strptime(prev.date_end, "%Y-%m-%d %H:%M:%S")
                        end_date_timedelta = end_date + datetime.timedelta(hours = task.lag_time)
                        if end_date_timedelta > datetime.datetime.now():
                            if prev.stage_id.state != 'done' and stage_my.state == 'open':
                                raise osv.except_osv(_('Warning!'), _('You can not start this task since previous task(s) is still not finished or lag time does now allow to make gaps.'))
                        else:
                            pass
                #if Finish to Start have only lead time then it allow to start task before completing previous task upto lead time.
                elif task.depend_type == 'fts' and task.lead_time > 0.0 and task.lag_time == 0.0:
                    for prev in task.previous_task_ids:
                        end_date = datetime.datetime.strptime(prev.date_end, "%Y-%m-%d %H:%M:%S")
                        if datetime.datetime.now()  > end_date:
                            end_date_diff=  datetime.datetime.now() - end_date
                        else:
                            end_date_diff= end_date - datetime.datetime.now()
                        hours = (end_date_diff.days * 24) + (end_date_diff.seconds / 60.00) / 60.00
                        if hours < task.lead_time:
                            pass
                        else:
                            if prev.stage_id.state != 'done' and stage_my.state == 'open':
                                raise osv.except_osv(_('Warning!'), _('You can not start this task since previous task(s) is still not finished or lead time specified on this task does now allow to make that gap. Please contact project manager.'))

                if task.depend_type == 'stf': #Start to Finish
                    for prev in task.previous_task_ids:
                        if prev.stage_id.state == 'draft' and stage_my.state == 'done':
                            raise osv.except_osv(_('Warning!'), _('You can not done this task since previous task(s) is still not started.'))

                if task.depend_type == 'sts': #Start to Start
                    for prev in task.previous_task_ids:
                        if prev.stage_id.state == 'draft' and stage_my.state == 'open':
                            raise osv.except_osv(_('Warning!'), _('You can not start this task since previous task(s) is still not started.'))
                
                if task.depend_type == 'ftf': #Finish to Finish
                    for prev in task.previous_task_ids:
                        if prev.stage_id.state != 'done' and stage_my.state == 'done':
                            raise osv.except_osv(_('Warning!'), _('You can not done this task since previous task(s) is still not finished.'))

        return super(project_task, self).write(cr, uid, ids, vals, context=context)
