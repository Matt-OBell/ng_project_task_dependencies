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

{
    'name' : 'Project Task Dependencies',
    'version': '1.0',
    "author" : "Mattobell",
    "website" : "http://www.mattobell.com",
    'description':"""
This module will allow user to setup start to finish, finish to start, start to start, finish to finish rules on task form.
User can also specify the Lead and Lag time.

After installing this module end date on task will become mandotary which will be used to calculate the rules of lead and lag timings along STS,STF,FTS,FTF.

- Allow multiple people to be assigned to a task
- Add those assigned to a task to be automatically added as followers of the task
- Automatically send emails on task activities to all followers of a task
 - eg when task is updated or the stage has changed
- When we list tasks in a project, we need to be able to drag task up and down to rearrange them.  We can either do this on task list or on Gantt Chart
- Gantt Chart is still an issue. We need to discuss more on this to make it fully functionally

Project/Configuration/Task Dependencies/Type of Dependencies
    """,
    'data':[
            'project_task_depend_view.xml',
            'data/dependencies_data.xml',
            'security/ir.model.access.csv'
            ],
    'depends':['project'],
    'category': 'Project Management',
    'installable':True,
    'auto_install':False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: