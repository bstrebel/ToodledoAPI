#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == '__main__':

    from pyutils import get_logger
    from tdapi import *

    logger = get_logger('example', 'DEBUG')
    td = ToodledoAPI.get_session()

    tasks = td.get_tasks(folder='[OxSync]')
    for task in tasks:
         logger.debug('%s' % (task))

    # task = ToodledoTask(title='New task', goal='New goal', folder='[OxSync]')
    # td.tasks.add(task)

    td.end_session()
    exit(0)


