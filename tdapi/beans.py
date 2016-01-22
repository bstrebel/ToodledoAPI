#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, json, re, requests

class ToodledoBean(object):
    
    MAP = {}
    DEFAULT = {}
    MODULE = 'beans'

    KEY = 'id'
    NAME = 'name'

    @classmethod
    def fields(cls, tag):

        if isinstance(tag, str):

            if tag == 'all':
                return filter(lambda k: k not in cls.DEFAULT, cls.MAP)
            elif tag == 'default':
                 return list(cls.DEFAULT)
            else:
                tag = tag.split(',')

        if isinstance(tag, list):

            fields = []
            for field in tag:
                if field in cls.MAP:
                    fields.append(field)
            return fields

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):

        self.__dict__['_data'] = data if data is not None else {}
        self.__dict__['_modified'] = None
        self.__dict__['_parent'] = parent
        self.__dict__['_tdapi'] = tdapi

        for key in kwargs:
            self.__dict__['_data'][key] = kwargs[key]

    def data(self, data):
        self.__dict__['_data'] = data if data is not None else {}
        self.__dict__['_modified'] = None

    def create(self, tdapi=None):
        tdapi = tdapi if tdapi else self._tdapi
        data = self.__dict__['_data']; create = {}
        for key in data:
            if key != 'id':
                create[key] = data[key]
        tdapi._request(self.MODULE, 'add', data=create)
        self.data(tdapi._request(self.MODULE, 'add', data=create))
        return self

    def update(self, tdapi=None):
        tdapi = tdapi if tdapi else self._tdapi
        self.data(tdapi._request(self.MODULE, 'edit', data=self.update_data))
        return self

    def load(self):
        pass

    def delete(self):
        deleted = self.tdapi._request(self.MODULE, 'delete', data={'id': self.id})
        id = deleted.get('deleted')
        if id is not None and id == self.id:
            if self.parent is not None:
                self.parent.delete(self.id)
            self.__dict__['_data'] = None
            self.__dict__['_modified'] = None

    @property
    def all_fields(self):
        """
        get all possible task attributes
        :return: array of field names from ToodledoTask.map
        """
        fields = filter(lambda k: k not in self.DEFAULT, self.MAP)
        return fields

    @property
    def used_fields(self):
        '''
        get list of attributes initialized by the last query
        :return: array of field names from the last get() query
        '''
        fields = filter(lambda f: self.MAP[f] is not None, self.all_fields)
        return fields

    @property
    def modified(self): return self.__dict__['_modified']

    @property
    def tdapi(self): return self.__dict__['_tdapi']

    @property
    def parent(self): return self.__dict__['_parent']

    @property
    def update_data(self):
        """
        update object for edit request
        :return: dictionary with modified attributes
        """
        update = {'id': self.id}
        if self.modified:
            for key in self.modified:
                update[key] = self[key]
        return update

    @property
    def update_json(self):
        """
        json representation of update object
        :return: json string of update object
        """
        import json
        return json.dumps(self.update_data, encoding='utf-8', ensure_ascii=False)

    def __str__(self):
        return u'%s: %s %s' % (self.__class__.__name__,
                               self.__dict__['_data'][self.KEY],
                               self.__dict__['_data'][self.NAME])

    def __repr__(self):
        return str(self.__dict__['_data'])

    def __getitem__(self, key):
        return self.__dict__['_data'].get(key) if self.__dict__['_data'] is not None else None
    
    def __setitem__(self, key, value):

        if isinstance(value, str):
            value = value.decode('utf-8')

        if self.__dict__['_data'] is None:
            self.__dict__['_data'] = {}

        if key in self.__dict__['data']:

            # modify existing attribute
            if self.__dict__['_data'][key] != value:
                if self.__dict__['_modified'] is None:
                    self.__dict__['_modified'] = {}
                self.__dict__['_modified'][key] = True

        self.__dict__['_data'][key] = value

    def __getattr__(self, key):
         return self.__getitem__(key)
    
    def __setattr__(self, key, value):
        if key in self._data or key in self.MAP:
            self.__setitem__(key, value)
        else:
            self.__dict__[key] = value

    def keys(self):
        return self.__dict__['_data'].keys()

    def values(self):
        return self.__dict__['_data'].values()

    def __contains__(self, key):
        return key in self.__dict__['_data']

    def __iter__(self):
        return iter(self.__dict__['_data'])

    def get(self, key):
        return self.__getitem__(key)

class ToodledoBeans(object):

    ITEMS = ToodledoBean
    MODULE = 'beans'
    LASTEDIT = 'lastedit_bean'

    def __init__(self, bean_class, data, tdapi=None):

        self._bean_class = bean_class
        self._beans = []
        self._tdapi = tdapi
        self._lastedit = None
        self._key_attributes = ['id', 'name']

        if isinstance(data, dict):
            if data.get('data'):
                self._lastedit = data.get('lastedit')
                data = data.get('data')

        for item in data:
            self._beans.append(bean_class(item, self._tdapi, self))

    def __str__(self):
        return '%s: %s items' % (self.__class__.__name__, len(self._beans))

    def __repr__(self):
        return str(self._beans)

    def data(self, data):
        self._beans = []
        for item in data:
            self._beans.append(self._bean_class(item, self._tdapi, self))

    def __iter__(self):
        return iter(self._beans)

    def __getitem__(self, index):
        '''
        index[] based access to beans
        :param index: search key (str) or numeric index for beans[]
        :return:
        '''
        if isinstance(index, int):
            return self._beans[index]
        else:
            if re.match('^\d+$', index):
                # convert id back to int
                index = int(index)
            return self.get(index)

    def get(self, key):

        if isinstance(key, str):
            key = key.decode('utf-8')

        for bean in self._beans:
            for attr in self._key_attributes:
                val = bean[attr]
                if type(val) == type(key):
                    if val == key:
                        return bean

        return None

    def delete(self, key):

        if isinstance(key, str):
            key = key.decode('utf-8')

        beans = []; found = False
        for bean in self._beans:
            if not found:
                for attr in self._key_attributes:
                    val = bean[attr]
                    if type(val) == type(key):
                        if val == key:
                            found = True
                            break
                if found:
                    continue

            beans.append(bean)

        return None


