#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tdapi import *

class ToodledoTask(ToodledoBean):
    MAP = {
        'id': {'default': None, 'type': int, 'used': False},
        'title': {'default': u'', 'type': int, 'used': False},
        'modified': {'default': 0, 'type': int, 'used': False},
        'completed': {'default': 0, 'type': int, 'used': False},
        'folder': {'default': 0, 'type': int, 'used': False},
        'context': {'default': 0, 'type': int, 'used': False},
        'goal': {'default': 0, 'type': int, 'used': False},
        'location': {'default': 0, 'type': int, 'used': False},
        'tag': {'default': 0, 'type': int, 'used': False},
        'startdate': {'default': 0, 'type': int, 'used': False},
        'duedate': {'default': 0, 'type': int, 'used': False},
        'duedatemod': {'default': 0, 'type': int, 'used': False},
        'starttime': {'default': 0, 'type': int, 'used': False},
        'duetime': {'default': 0, 'type': int, 'used': False},
        'remind': {'default': 0, 'type': int, 'used': False},
        'repeat': {'default': u'', 'type': int, 'used': False},
        'status': {'default': 0, 'type': int, 'used': False},
        'star': {'default': 0, 'type': int, 'used': False},
        'priority': {'default': 0, 'type': int, 'used': False},
        'length': {'default': 0, 'type': int, 'used': False},
        'timer': {'default': 0, 'type': int, 'used': False},
        'added': {'default': 0, 'type': int, 'used': False},
        'note': {'default': u'', 'type': int, 'used': False},
        'parent': {'default': 0, 'type': int, 'used': False},
        'children': {'default': 0, 'type': int, 'used': False},
        'order': {'default': 0, 'type': int, 'used': False},
        'meta': {'default': None, 'type': int, 'used': False},
        'previous': {'default': 0, 'type': int, 'used': False},
        'attachment': {'default': 0, 'type': int, 'used': False},
        'shared': {'default': 0, 'type': int, 'used': False},
        'addedby': {'default': u'', 'type': int, 'used': False},
        'via': {'default': 0, 'type': int, 'used': False},
        'attachments': {'default': 0, 'type': int, 'used': False}}

    DEFAULT = {'id': None, 'title': u'', 'modified': 0, 'completed': 0}

    KEY = 'id'
    NAME = 'title'

    STATUS = ['None', 'Next', 'Active', 'Planning', 'Delegated',
              'Waiting', 'Hold', 'Postponed', 'Someday', 'Canceled', 'Reference']

    PRIORITY = {'Negative': -1, 'Low': 0, 'Medium': 1, 'High': 2, 'Top': 3}

    PERMALINK = 'https://www.toodledo.com/tasks/index.php?x=%s#task_%s'

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):
        ToodledoBean.__init__(self, data, tdapi, parent, **kwargs)

    @property
    def _time(self): return self.modified * 1000

    @property
    def _start_date(self): return self.startdate * 1000 if self.startdate else None

    @property
    def _due_date(self): return self.duedate * 1000 if self.duedate else None

    @property
    def _start_time(self): return self.starttime * 1000 if self.starttime else None

    @property
    def _due_time(self): return self.duetime * 1000 if self.duetime else None

    @property
    def _date_completed(self): return self.completed * 1000 if self.completed else None

    @property
    def _remind_date(self):
        if self.remind:
            due = (self.duedate or 0) + (self.duetime or 0)
            return (due - (self.remind * 60)) * 1000
        return None

    @property   # evernote compatible representation of categories
    def tagNames(self): return self.tag_names('ascii')


    def tag_names(self, encoding=None):
        '''
        categories spliited into a list of names
        :param encoding: use ascii for Evernote compatible encoding
        :return: list of encoded tag names
        '''
        names = []
        if self.tag:
            for tag in self.tag.split(','):
                name = tag
                if encoding is 'ascii':
                    if isinstance(tag, unicode):
                        name = tag.encode('utf-8')
                names.append(name)
        return names

    def get_url(self, x_id):
        return self.PERMALINK % (x_id, self.id)

class ToodledoTasks(ToodledoBeans):

    def __init__(self, data=None, tdapi=None):

# region Adjust data offset
        item = None

        if isinstance(data, dict):
            # loaded from cache
            if data.get('data'):
                if len(data['data']) > 0:
                    if data['data'][0].get('total'):
                        data['data'] = data['data'][1:]
                        item = data['data'][0]

        elif isinstance(data, list):
            # returned from service request
            if len(data) > 0:
                if data[0].get('total'):
                    data = data[1:]
                    item = data[0]
        else:
            raise ValueError
# endregion

        # dynamic update of bean class map
        # from first data item
        if item is not None:
            for key in item:
                ToodledoTask.MAP[key]['used'] = True

        ToodledoBeans.__init__(self, ToodledoTask, data, tdapi)

        # index[] based access to tasks[bean]
        self._key_attributes = ['id', 'title']
