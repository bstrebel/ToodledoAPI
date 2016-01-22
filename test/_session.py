#!/usr/bin/env python
# -*- coding: utf-8 -*-

# fields = ToodledoTask.fields('all')
# fields = ToodledoTask.fields('default')
# fields = ToodledoTask.fields(['id', 'folder', 'priority'])

# toodledo = ToodledoAPI()
# account =  toodledo.get_account_info()
# print account
#
# folders = toodledo.get_folders()
# for folder in folders:
#     print folder
#
# #task = toodledo.get_tasks(id=23774181, fields=ToodledoTask.fields('all'))[0]
# task = toodledo.get_task(23774181)
# task.note = 'Task note'
# task.tag = '[Tag]'

# task.update()

# for task in tasks:
#     print task.id, task['title']
#
# task = tasks.get(u'New unicode title [ÄÖÜ]')
# task['title'] = u'Changed unicode title [ÄÖÜ]'
#
# task_update = [{"id": 23774181, "title": u"Changed unicode title [ÄÖÜ]"}]
# task_json = json.dumps(task_update, encoding='utf-8', ensure_ascii=False)
# params = {'tasks': task_json, 'fields': 'folder,star'}
# response = toodledo._request('tasks', 'edit', params=params)


# region __Main__
if __name__ == '__main__':

    # import sys, codecs
    # #from kitchen.text.converters import getwriter
    # UTF8Writer = codecs.getwriter('utf8')
    # sys.stdout = UTF8Writer(sys.stdout)

   # import sys
    # reload(sys)
    # sys.setdefaultencoding('utf-8')

    from tdapi import *

    toodledo = ToodledoAPI()


    #tasks = toodledo.get_tasks(fields=','.join(ToodledoTask.fields('all')))

    # print toodledo.account.email
    for task in toodledo.tasks:
        print task.id

    exit(0)

    toodledo = ToodledoAPI()
    toodledo.update_cache()
    # print toodledo._cache
    exit(0)

    account =  toodledo.get_account_info()
    print account

    # new_folder = ToodledoFolder({'name': u'Übersicht', 'private': 1}, toodledo)
    # if new_folder.create(toodledo):
    #     print new_folder

    folders = toodledo.get_folders()
    folder = folders[u'Übersicht']
    if folder is not None:
        folder.delete()

    for folder in folders:
        print folder.id


    # folder = folders.get('Übersicht')
    # if folder:
    #     folder.name = 'Übersicht'
    #     folder.id = 0
    #     folder['private'] = 'X'
    #     folder.update(toodledo)


    # task = toodledo.get_tasks(id=23774181, fields=ToodledoTask.fields('all'))[0]
    # task = toodledo.get_task(23774181)

    # task.note = 'Task note'
    # task.tag = '[Tag]'
    # task.update()

    exit(0)
# endregion


