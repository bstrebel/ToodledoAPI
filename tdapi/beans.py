#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, json, re, requests, uuid, time
from collections import OrderedDict
from pyutils import utf8, strflocal
from tdapi import ToodledoAPI

#########################
# Generic toodledo bean #
#########################

class ToodledoBean(object):
    
    MAP = {}
    DEFAULT = {}
    MODULE = 'beans'

    KEY = 'id'
    NAME = 'name'
    KEY_ATTRIBUTES = [KEY, NAME]

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
        self.__dict__['_properties'] = None
        self.__dict__['_modified'] = None
        self.__dict__['_deleted'] = None
        self.__dict__['_created'] = None
        self.__dict__['_parent'] = parent
        self.__dict__['_tdapi'] = tdapi or ToodledoAPI.get_session()
        self.__dict__['_uuid'] = str(uuid.uuid1())

        for key in kwargs:
            self.__setitem__(key, kwargs[key])

    def properties(self):
        '''
        get @properties of this instance and store them in self._properties
        :return: cached self._properties
        '''
        if self.__dict__['_properties'] is None:
            self.__dict__['_properties'] = []
            for k,v in self.__class__.__dict__.iteritems():
                if isinstance(v, property):
                    self.__dict__['_properties'].append(k)
        return self.__dict__['_properties']

    def data(self, data, **kwargs):
        '''
        update data of existing bean
        :param data: new data dictionary {'title': 'new_title'}
        :param kwargs: more attributes from args e.g. title='new title' ...
        :return: the updated bean
        '''
        self.__dict__['_data'] = data if data is not None else {}
        self.__dict__['_modified'] = None
        self.__dict__['_deleted'] = False

        for key in kwargs:
            self.__setitem__(key, kwargs[key])

        return self

    @property
    def _logger(self): return self._tdapi.logger

    @property
    def _id(self): return self.id or self._uuid

    @property
    def _key(self): return utf8(self[self.NAME])

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
        fields = filter(lambda f: self.MAP[f].get('used', False), self.all_fields)
        return fields

    @property
    def bean_data(self):
        '''
        just all bean data
        :return: the bean data dictionary
        '''
        return self.__dict__['_data']

    @property
    def update_data(self):
        """
        update object for edit request
        :return: dictionary with modified attributes only
        """
        update = {'id': self.id}
        if self._modified:
            for key in self._modified:
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

        return u'%s: %s %s' % (utf8(self.__class__.__name__),
                               utf8(self._id),
                               utf8(self._key))

    def __repr__(self):
        return u'%s data=%s' % (self.__str__(), utf8(self.__dict__['_data']))

    def __getitem__(self, key):
        return self.__dict__['_data'].get(key) if self.__dict__['_data'] is not None else None
    
    def __setitem__(self, key, value):

        # if key in self.properties():
        #     setattr(self, key, value)
        #     return

        if isinstance(value, str):
            value = utf8(value)

        if self.__dict__['_data'] is None:
            self.__dict__['_data'] = {}

        if key in ['folder', 'context', 'goal', 'location']:
            self._logger.debug('Processing special attribute [%s]' % (key))
            value = self._tdapi.get_list_item(key + 's', value)._id

            # call = getattr(self._tdapi, 'get_' + key)
            # if call:
            #     result = call(value)
            #     if result:
            #         value = result._id

        if key in self.__dict__['_data'] and key != 'modified':

            # modify existing attribute
            if self.__dict__['_data'][key] != value:
                self._logger.debug('Mofify bean attribute [%s]' % (key))
                if self.__dict__['_modified'] is None:
                    self.__dict__['_modified'] = {}
                self.__dict__['_modified'][key] = True

                self.__dict__['_data']['modified'] = int(time.time())

                if self.__dict__['_parent'] is not None:
                    self.__dict__['_parent']._modified[self.id] = self

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

    def delete(self):
        if self.__dict__['_parent'] is not None:
            self.__dict__['_parent'].delete(self.id)
        self.__dict__['_deleted'] = True

    def update_modified(self):
        self.__dict__['_data']['modified'] = int(time.time())

####################################
# Generic toodledo bean collection #
####################################

class ToodledoBeans(object):

    ITEMS = ToodledoBean
    MODULE = 'beans'
    LASTEDIT = 'lastedit_bean'

    def __init__(self, bean_class, data, tdapi=None):

        self._bean_class = bean_class
        self._beans = []
        self._tdapi = tdapi or ToodledoAPI.get_session()
        self._lastedit = None
        self._deleted = OrderedDict()
        self._modified = OrderedDict()
        self._created = OrderedDict()
        self._uuid_map = {}
        self._key_attributes = ['id', 'name']
        self._filter = lambda bean: True

        if isinstance(data, dict):
            # loaded from cache ...
            if data.get('data') is not None:
                self._lastedit = data.get('lastedit')
                data = data.get('data')

        for item in data:
            # generate a list of typed beans from data
            self._beans.append(bean_class(item, self._tdapi, self))

    @property
    def count(self):
        return len(self._beans)

    @property
    def deleted(self):
        return self._deleted

    def __str__(self):
        return u'%s: %s items' % (utf8(self.__class__.__name__), len(self._beans))

    def __repr__(self):
        return u'%s beans=%s' % (self.__str__(), map(lambda bean: bean.__str__(), self._beans))

    def data(self, data):
        self._beans = []
        self._modified = OrderedDict()
        self._deleted = OrderedDict()
        self._created = OrderedDict()
        for item in data:
            self._beans.append(self._bean_class(item, self._tdapi, self))

    def add(self, bean):
        if isinstance(bean, self._bean_class):
            # bean._modified = {}
            # for attr in bean.__dict__['_data']:
            #     bean._modified[attr] = True
            bean._created = True
            bean._tdapi = bean._tdapi or self._tdapi
            bean._parent = self
            bean.update_modified()
            self._beans.append(bean)
            self._created[bean._uuid] = bean
            return bean

    def __iter__(self):
        return iter(filter(self._filter, self._beans))

    def __getitem__(self, index):
        '''
        index[] based access to beans
        :param index: search key (str) or numeric index for beans[]
        :return:
        '''
        if isinstance(index, int) and index < self.count:
            # assuming toodledo ID is always greater than the number of tasks
            return self._beans[index]
        else:
            return self.get(index)

    def get(self, key):
        '''
        get a bean from the collection
        :param key: numeric id or string to search in self._key_attributes
        :return: the bean found or None
        '''
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
        '''
        delete a bean from the collection
        :param key: numeric id or string to search in self._key_attributes
        :return: True if key was found in collection
        '''
        if isinstance(key, str):
            key = utf8(key)

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
                    bean._deleted = True
                    self._deleted[bean.id] = bean
                    continue

            beans.append(bean)

        return found


