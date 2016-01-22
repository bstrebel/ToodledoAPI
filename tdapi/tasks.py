#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
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

    def __init__(self, data=None, tdapi=None, parent=None):
        ToodledoBean.__init__(self, data, tdapi, parent)

    def update(self):
        fields = ','.join(self.used_fields)
        json = self.update_json()
        data = {'tasks': json, 'fields': fields}
        response = self.tdapi._request('tasks', 'edit', data=data)
        pass

    def load(self):
        fields = ','.join(self.all_fields)
        params = {'id': self.id, 'fields': fields}
        response = self.tdapi._request('tasks', 'get', params=params)

    @property
    def time(self):
        return self.modified * 1000

class ToodledoTasks(ToodledoBeans):

    def __init__(self, data=None, tdapi=None):

        item = None
        if isinstance(data, dict):
            # loaded from cache
            if data.get('data'):
                if len(data['data']) > 0:
                    if data['data'][0].get('total'):
                        data['data'] = data['data'][1:]
                        item = data['data'][0]
        elif isinstance(data, list):
            if len(data) > 0:
                if data[0].get('total'):
                    data = data[1:]
                    item = data[0]
        else:
            raise ValueError

        # dynamic update of bean class map
        if item is not None:
            for key in item:
                ToodledoTask.MAP[key] = True

        ToodledoBeans.__init__(self, ToodledoTask, data, tdapi)

        # index[] based access to tasks[bean]
        self._key_attributes = ['id', 'title']
