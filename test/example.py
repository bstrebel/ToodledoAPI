#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

if __name__ == '__main__':

    from pyutils import get_logger
    from tdapi import *

    logger = get_logger('example', 'DEBUG')
    td = ToodledoAPI.get_session()

    tasks = td.get_tasks(folder=None)
    for task in tasks:
         logger.debug('%s' % (task))

    DAY = 24*60*60
    timestamp = int(time.time())

# region Toodledo task attributes
        # id, title, modified, completed,
        # folder, context, goal, location, tag,
        # startdate, duedate, duedatemod, starttime, duetime,
        # remind, repeat,
        # status, star, priority,
        # length, timer, added, note,
        # parent, children, order,
        # meta, previous, attachment,
        # shared, addedby, via, attachments
# endregion

    # task = ToodledoTask(title='TASK')
    #
    # task.note = 'NOTE'
    # task.context = 'CONTEXT'
    # task.goal = 'PROJECT'
    # task.folder = 'API'
    # task.location = 'LOCATION'
    # task.tag = 'TAG'
    # task.startdate = timestamp  # - (timestamp % DAY)
    # task.starttime = 0
    # task.duedate = task.startdate + (DAY * 2)
    # task.duetime = 0
    # task.remind = 12 * 60  # 12 hours
    # task.status = ToodledoTask.STATUS.index('Active')
    # task.priority = ToodledoTask.PRIORITY['High']
    # task.star = True
    #
    # task.tag = 'NEW_TAG'
    #
    # td.tasks.add(task)

    td.end_session()
    exit(0)
