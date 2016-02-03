#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, requests, json, re, codecs, logging

class ToodledoAPI(object):

    # default settings
    _SERVICE_URL = 'api.toodledo.com/3'
    _SESSION_CACHE_DIR = '~/.tdapi'

    _session = None

    @staticmethod
    def get_session(cache='~/.tdapi', client_id=None, client_secret=None, logger=None):

        if ToodledoAPI._session is None:

            client_id = client_id or os.environ.get('TOODLEDO_CLIENT_ID')
            client_secret = client_secret or os.environ.get('TOODLEDO_CLIENT_SECRET')
            ToodledoAPI._session = ToodledoAPI(cache, client_id, client_secret, logger)
            if ToodledoAPI._session is not None:
                ToodledoAPI._session.update_cache()

        return ToodledoAPI._session

    def __init__(self, cache='~/.tdapi', client_id=None, client_secret=None, logger=None):

# region Logging
        from pyutils import get_logger, LogAdapter
        if logger is None:
            self._logger = get_logger('tdapi', 'DEBUG')
        else:
            self._logger = logger
        self._adapter = LogAdapter(self._logger, {'package': 'tdapi'})
# endregion

        self._client_id = client_id or os.environ.get('TOODLEDO_CLIENT_ID')
        self._client_secret = client_secret or os.environ.get('TOODLEDO_CLIENT_SECRET')

        self._cache_dir = os.path.expanduser(cache)
        self._cache = {'session': None, 'account': None, 'lists': None, 'tasks': None}

        self._offline = None

        self._account = None
        self._lists = None
        self._tasks = None

        from tdapi import ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations
        from tdapi import ToodledoFolder, ToodledoContext, ToodledoGoal, ToodledoLocation

        self._class_map = {'folders': {'collection': ToodledoFolders, 'item': ToodledoFolder, 'auto': True},
                           'contexts': {'collection': ToodledoContexts, 'item': ToodledoContext, 'auto': True},
                           'goals': {'collection': ToodledoGoals, 'item': ToodledoGoal, 'auto': True},
                           'locations': {'collection': ToodledoLocations, 'item': ToodledoLocation, 'auto': True}}

        # load cache files
        for key in self._cache:
            fn = self.cache_file(key)
            if os.path.isfile(fn):
                with codecs.open(fn, 'r', encoding='utf-8') as fh:
                    self._cache[key] = json.load(fh)

    def cache_file(self, key):
        return self._cache_dir + '/tdapi.' + key

    @property
    def logger(self):return self._adapter

    @property
    def session(self):
        return self._cache['session']

    @session.setter
    def session(self, value):
        self._cache['session'] = value

    @property
    def authenticated(self): return self.access_token is not None

    @property
    def offline(self): return self._offline == True

    @property
    def online(self): return self._offline == False

    @property
    def access_token(self):
        return self.session.get('access_token') if isinstance(self.session, dict) else None

    @property
    def refresh_token(self):
        return self.session.get('refresh_token') if isinstance(self.session, dict) else None

    @property
    def expired(self):
        return bool((int(time.time()) - self.session.get('time_stamp',0)) > self.session.get('expires_in', 0))

    #################################
    # Session collection properties #
    #################################

    @property
    def account(self):
        if self._account is None:
            self._account = self._get_account_info()
        return self._account

    @property
    def tasks(self):
        from tdapi import ToodledoTasks
        if self._tasks is None:
            self._update_tasks_cache()
            self._tasks = ToodledoTasks(self._cache['tasks'], self)
        return self._tasks

    @property
    def folders(self): return self._lists.get('folders')

    @property
    def contexts(self): return self._lists.get('contexts')

    @property
    def goals(self): return self._lists.get('goals')

    @property
    def locations(self): return self._lists.get('locations')

    #######################
    # Generate OAuth2 URL #
    #######################

    def _authorize(self):
        url = 'https://%s/account/authorize.php' % (ToodledoAPI._SERVICE_URL)
        params = {'response_type': 'code', 'client_id' : self._client_id, 'state': '569cc6ba091a1', 'scope': 'basic tasks notes'}
        # response = requests.get(url, params=params)

    def _refresh(self):
        url = 'https://%s:%s@%s/account/token.php' % (self._client_id, self._client_secret, ToodledoAPI._SERVICE_URL)
        data = {'grant_type': 'refresh_token', 'refresh_token': self.refresh_token}
        self.session = self._response(requests.post(url, data=data))
        if self.session is not None:
            self.session['time_stamp'] = int(time.time())
            self.logger.debug('Refresh: %s' % (self.session))
            with codecs.open(self.cache_file('session'), 'w', encoding='utf-8') as fp:
                json.dump(self.session, fp, indent=4, ensure_ascii=False, encoding='utf-8')

    ##########################
    # Tasks cache operations #
    ##########################

    def update_cache(self, reset=False):

        if reset:
            for key in self._cache:
                if key == 'session': continue
                self._cache[key] = None
                fn = self.cache_file(key)
                if os.path.isfile(fn):
                    os.remove(fn)

        self._account = self._get_account_info()
        self._update_lists_cache()
        self._update_tasks_cache()

    def end_session(self):
        if self._update_lists():
            # allow creation of new list entries
            # in the toodledo server database
            time.sleep(5)
        self._update_tasks()

    ###############################
    # High level tasks operations #
    ###############################

    def get_tasks(self, folder=None):
        tasks = self.tasks
        if tasks is not None:
            if folder:
                if self.folders.get(folder):
                    id = self.folders[folder].get('id')
                    if id:
                        tasks._filter = lambda bean: bean['folder'] == id
                else:
                    self.logger.error('Invalid toodle folder [%s]' % (folder))

# region Test filter evaluation
                # if isinstance(folder, dict):
                #     key = folder.keys()[0]
                #     val = folder[key]
                #     tasks._filter = lambda bean: bean[key] == val
                # elif isinstance(folder, str):
                #     tasks._filter = eval(folder)
                # else:
                #     tasks._filter = folder
# endregion
        return tasks

    def get_task(self, id):
        return self.tasks[id]

    def delete_task(self, id):
        return self.tasks.delete(id)

    def create_task(self, **kwargs):
        from tdapi import ToodledoTask
        todo = ToodledoTask(**kwargs)
        return self.tasks.add(todo)

    ###############################
    # High level lists operations #
    ###############################

    def get_list_item(self, list, item, auto=None):
        from tdapi import ToodledoFolder, ToodledoContext, ToodledoGoal, ToodledoLocation
        if isinstance(item, self._class_map[list]['item']):
            return item
        if self._lists[list].get(item):
            return self._lists[list][item]
        else:
            if auto is None:
                auto = self._class_map[list]['auto']
            if auto:
                return self._lists[list].add(self._class_map[list]['item'](name=item))
        return None

    def create_list_item(self, list, **kwargs):
        item = self._class_map[list]['item'](**kwargs)
        return self._lists[list].add(item)

    def delete_list_item(self, list, id):
        return self._lists[list].add(id)

    ###########################################
    # Update toodledo server from local cache #
    ###########################################

    def _check_list_id(self, data):
        for key in ['folder', 'context', 'goal', 'location']:
            list = key + 's'
            if data.get(key) and isinstance(data[key], str):
                if self._lists[list]._uuid_map.get(data[key]):
                    data[key] = self._lists[list]._uuid_map[data[key]]
        return data

    def _update_lists(self):

        delay = False
        for list in self._class_map.keys():

            self._lists[list]._uuid_map = {}

            for key in self._lists[list]._deleted.keys():
                self.logger.debug('Delete %s item %s' % (list, key))
                result = self._delete_item(list, key)

            for uuid, bean in self._lists[list]._created.iteritems():
                self.logger.debug('Create %s item [%s]: %s' % (list, uuid, bean.name))
                result = self._add_item(list, bean.bean_data)
                if result:
                    # update with server response
                    bean.data(result[0])
                    #self.logger.debug('Created: %s' % (bean._data))
                    # add entry to _uuid_map
                    self._lists[list]._uuid_map[uuid] = bean.id
                    self.logger.debug('Add entry to %s uuid_map: [%s] => [%s]' % (list, uuid, bean.id))
                    delay = True

            for id, bean in self._lists[list]._modified.iteritems():
                if id in self._lists[list]._uuid_map:
                    self.logger.debug('Update skipped for %s item [%s]: %s', list, id, bean.name)
                else:
                    self.logger.debug('Update %s item %s: %s' % (list, id, bean.name))
                    result = self._edit_item(list, bean.update_data)
                    if result:
                        bean.data(result[0])

        return delay

    def _update_tasks(self):

        if self._tasks:

            # process deleted task from cache
            if self._tasks._deleted:
                self.logger.debug('Delete tasks: %s' % (self.tasks._deleted.keys()))
                result = self._delete_tasks(self.tasks._deleted.keys())
                if result:
                    for entry in result:
                        # remove deleted items from modified/created
                        if entry.get('id'):
                            bean_id = entry.get('id')
                            self.logger.debug('Delete confirmed for task [%s]: %s' % (bean_id, self._tasks[bean_id].title))
                            if self._tasks._modified.get(bean_id):
                                self.logger.debug('Remove [%s] from modified hash' % (bean_id))
                                del(self._tasks._modified[bean_id])
                            if self._tasks._created.get(bean_id):
                                self.logger.debug('Remoe [%s] from created hash' % (bean_id))
                                del(self._tasks._created[bean_id])
                        else:
                            self.logger.error('Result: %s' % (result))


            # create new tasks from ordered dict
            data = []
            for uuid,bean in self._tasks._created.iteritems():
                self.logger.debug('Create for [%s]: %s' % (uuid, bean.title))
                data.append(self._check_list_id(bean.bean_data))
            if len(data) > 0:
                result = self._add_tasks(data)
                if result:
                    index = 0
                    for uuid, bean in self._tasks._created.iteritems():
                        if result[index].get('id'):
                            bean_id = result[index].get('id')
                            self.logger.debug('Update [%s] with [%s]: %s' % (uuid, bean_id, result[index]))
                            self._tasks._uuid_map[uuid] = bean_id
                            bean.data(result[index])
                            self.logger.debug('Created: %s' % (bean._data))
                            #bean.id = bean_id
                            #bean.modified = result[index].get('modified')
                            # cleanup _modified list because of bean update (?)
                            if self._tasks._modified.get(bean.id):
                                del(self._tasks._modified[bean.id])
                        else:
                            self.logger.error('Result: %s' % (result[index]))
                        index += 1

            # update modified tasks from cache
            data = []
            for uuid,bean in self._tasks._modified.iteritems():
                if uuid is not None:
                    data.append(self._check_list_id(bean.update_data)) # if uuid is not None (?)
                    self.logger.debug('Create for [%s]: %s' % (uuid, bean.name))
                else:
                    self.logger.warning('Skipping bogus entry in tasks._modified dict: %s' % (bean._data))
            if len(data) > 0:
                result = self._edit_tasks(data)
                if result:
                    index = 0
                    for uuid, bean in self._tasks._modified.iteritems():
                        if result[index].get('id'):
                            bean_id = result[index].get('id')
                            self.logger.debug('Update [%s] with [%s]: %s' % (uuid, bean_id, bean))
                            bean.data(result[index])
                            self.logger.debug('Updated: %s' % (bean._data))
                            # bean.modified = result[index].get('modified')
                        else:
                            self.logger.error('Result: %s' % (result[index]))
                        index += 1

    #############################################
    # Update cache from toodledo server changes #
    #############################################

    def _get_account_info(self):
        from tdapi import ToodledoAccount
        response = self._request('account', 'get')
        if response:
            self._cache['account'] = response
            with codecs.open(self.cache_file('account'), 'w', encoding='utf-8') as fp:
                json.dump(response, fp, indent=4, ensure_ascii=False, encoding='utf-8')
        return ToodledoAccount(response, self)

    def _update_lists_cache(self):
        
        from tdapi import ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations

        if self._lists is None: self._lists = {}
        if self._cache['lists'] is None: self._cache['lists'] = {}
        cache = self._cache['lists']

        for list in [ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations]:

            if cache.get(list.MODULE):
                if cache[list.MODULE].get('lastedit'):
                    if cache[list.MODULE]['lastedit'] >= self.account[list.LASTEDIT]:
                        self._lists[list.MODULE] = list(cache[list.MODULE], self)
                        continue

            if cache.get(list.MODULE) is None: cache[list.MODULE] = {}
            cache[list.MODULE]['data'] = self._request(list.MODULE, 'get')
            cache[list.MODULE]['lastedit'] = self.account[list.LASTEDIT]
            self._lists[list.MODULE] = list(cache[list.MODULE], self)

        with codecs.open(self.cache_file('lists'), 'w', encoding='utf-8') as fp:
            json.dump(cache, fp, indent=4, ensure_ascii=False, encoding='utf-8')

    def _update_tasks_cache(self):

        from tdapi import ToodledoTasks, ToodledoTask

        data = None
        cache = self._cache['tasks']

        if cache is None:
            data = self._request('tasks', 'get', params={'fields': ','.join(ToodledoTask.fields('all'))})
        else:
            if cache['lastedit'] < self.account.lastedit_task:

                deleted = {}
                response = self._request('tasks', 'deleted', params={'after': cache['lastedit']})
                if response and len(response) > 1:
                    num_deleted = response[0].get('num')
                    for item in response[1:]:
                        if item.get('id'):
                            deleted[item['id']] = item

                modified = {}
                response = self._request('tasks', 'get', params={'fields': ','.join(ToodledoTask.fields('all')),
                                                                 'after': cache['lastedit']})

                if response and len(response) > 1:
                    num_modified = response[0].get('num')
                    for item in response[1:]:
                        if item.get('id'):
                            modified[item['id']] = item

                data = ['SKIP']

                if cache.get('data') is not None and isinstance(cache['data'], list):

                    # check modified and deleted items
                    for item in cache['data']:
                        if item.get('id'):
                            id = item['id']
                            if id in deleted:
                                continue
                            if id in modified:
                                data.append(modified[id])
                                del(modified[id])
                                continue
                            data.append(item)

                    # add new items
                    for id, item in modified.iteritems():
                        data.append(item)
                else:
                    self.logger.critical('Cannot update Toodledo task_cache!')
                    raise Exception('Cannot update Toodledo task_cache!')

        if data is not None:
            cache = {'lastedit': self.account.lastedit_task, 'data': data[1:]}
            self._tasks = ToodledoTasks(cache, self)
            with codecs.open(self.cache_file('tasks'), 'w', encoding='utf-8') as fp:
                json.dump(cache, fp, indent=4, ensure_ascii=False, encoding='utf-8')

    ##################################
    # Low level web service requests #
    ##################################

    def _response(self, response):
        """
        Post process web request response
        :param response: web request response
        :return: json object content
        """
        from tdapi import ToodledoRequestError
        if response is not None:
            if response.content is not None:
                #self.logger.debug("Response content: [%s]" % (response.content))
                #if response.content.startswith('{'):
                content = response.json(encoding='UTF-8')
                self.logger.debug("Response json content: %s" % (response.content))
                if 'errorCode' in content:
                    raise ToodledoRequestError(content)
                return content
            return response.content
        return None

    def _url(self, module, action):
        """
        Pre process web request
        :param module:
        :param action:
        :return: formatted URL
        """
        url = 'https://%s/%s/%s.php' % (ToodledoAPI._SERVICE_URL, module, action)
        self.logger.debug("Request url: %s" % (url))
        return url

    def _params(self, params=None):
        if params is None: params = {}
        params['access_token'] = self.access_token
        #params['f'] = 'json'
        self.logger.debug("Request params: %s" % (params))
        return params

    def _request(self, module, action, params=None, data=None):
        try:
            self._offline = True
            if self.expired: self._refresh()
            #self.logger.debug('Request call: [%s] with body %s' % (call.func_name, data))
            url = self._url(module, action)
            params = params=self._params(params)
            if data is not None:
                self.logger.debug('Request body: %s' % (data))
                response = requests.post(url, params=params, data=data)
            else:
                response = requests.get(url, params=params)
            self.logger.debug('Request url: %s' % (response.request.path_url))
            if response.status_code == 401:
                self._refresh()
                response = requests.get(url, params=params, data=data)
                self.logger.debug('Request url: %s' % (response.request.path_url))
        except requests.exceptions.RequestException as e:
            self.logger.error("Request exception: %s" % (e))
            return None
        self._offline = False
        return self._response(response)

    ####################################
    # Low level tasks service requests #
    ####################################

    def _bulk_request(self, module, operation, items, increment=50):

        result = []
        self.logger.debug('Bulk request for %d items total' % (len(items)))
        for offset in range(0, len(items), increment):
            last = offset+increment
            self.logger.debug('Processing slice [%d:%d]' % (offset, last))
            slice = items[offset:last]
            self.logger.debug('Processing slice [%d:%d] with %d items' % (offset, last, len(slice)))
            data = json.dumps(slice, encoding='utf-8', ensure_ascii=False)
            sub = self._request(module, operation, data={module: data})
            if len(slice) != len(sub):
                self.logger.error('Bulk request returned with %d items: %s' % (len(sub), sub))
            else:
                self.logger.debug('Bulk request returned with %d items' % (len(sub)))
                result.extend(sub)
        self.logger.debug('Bulk request completed with %d items total' % (len(result)))
        return result

    def _get_tasks(self, **kwargs):
        from tdapi import ToodledoTasks
        return ToodledoTasks(self._request('tasks', 'get', params=kwargs), self)

    def _get_task(self, id, **kwargs):
        from tdapi import ToodledoTask
        kwargs['id'] = id
        # fields=ToodledoTask.fields('all')
        data = self._request('tasks', 'get', params=kwargs)
        return ToodledoTask(data[1], self)

    def _delete_tasks(self, id_list, bulk=50):
        if isinstance(id_list, str):
            id_list = list(id_list.split(','))
        else:
            id_list = list(map(lambda i: str(i), id_list))

        if len(id_list) > bulk:
            return self._bulk_request('tasks', 'delete', id_list, bulk)
        else:
            tasks = json.dumps(id_list)
            result = self._request('tasks', 'delete', data={'tasks': tasks})
            return result

    def _edit_tasks(self, task_list, bulk=50):
        if len(task_list) > bulk:
            return self._bulk_request('tasks', 'edit', task_list, bulk)
        else:
            tasks = json.dumps(task_list, encoding='utf-8', ensure_ascii=False)
            result = self._request('tasks', 'edit', data={'tasks': tasks})
            return result

    def _add_tasks(self, task_list, bulk=50):
        if len(task_list) > bulk:
            return self._bulk_request('tasks', 'add', task_list, bulk)
        else:
            tasks = json.dumps(task_list, encoding='utf-8', ensure_ascii=False)
            result = self._request('tasks', 'add', data={'tasks': tasks})
            return result

    ##############################
    # Low level lists operations #
    ##############################

    def _get_list_items(self, list):
        result = self._request(list, 'get')
        return result

    def _get_list_items(self, list):
        # from tdapi import ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations
        data = self._request(list, 'get')
        return self._class_map[list]['collection'](data, self)

    def _delete_item(self, list, id):
        result = self._request(list, 'delete', data={'id': id})
        return result

    def _edit_item(self, list, data):
        result = self._request(list, 'edit', data=data)
        return result

    def _add_item(self, list, data):
        result = self._request(list, 'add', data=data)
        return result

# region __Main__
if __name__ == '__main__':

    from tdapi import *

    td = ToodledoAPI.get_session()
    print td.account.email

    exit(0)
# endregion


