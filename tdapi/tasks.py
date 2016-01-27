#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tdapi import *

class ToodledoTask(ToodledoBean):

    MAP = {'id': None, 'title': None, 'modified': None, 'completed': None,
           'folder': None, 'context': None, 'goal': None, 'location': None, 'tag': None,
           'startdate': None, 'duedate': None, 'duedatemod': None, 'starttime': None, 'duetime': None,
           'remind': None, 'repeat': None,
           'status': None, 'star': None, 'priority': None,
           'length': None, 'timer': None, 'added': None, 'note': None,
           'parent': None, 'children': None, 'order': None,
           'meta': None, 'previous': None, 'attachment': None,
           'shared': None, 'addedby': None, 'via': None, 'attachments': None}

    DEFAULT = {'id': None, 'title': None, 'modified': None, 'completed': None}

    KEY = 'id'
    NAME = 'title'

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):
        ToodledoBean.__init__(self, data, tdapi, parent, **kwargs)

    @property
    def _time(self): return self.modified * 1000

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
                ToodledoTask.MAP[key] = True

        ToodledoBeans.__init__(self, ToodledoTask, data, tdapi)

        # index[] based access to tasks[bean]
        self._key_attributes = ['id', 'title']
