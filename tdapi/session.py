#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, requests, json, re, codecs, logging


class ToodledoAPI(object):

    _SERVICE_URL = 'api.toodledo.com/3'
    _SESSION_FILE = '~/.tdapi.oauth2'

    _session = None

    @staticmethod
    def get_session(session='~/.tdapi.oauth2', cache='~/.tdapi.cache', tasks_cache='~/.tdapi.tasks',
                    client_id=None, client_secret=None, logger=None):

        if ToodledoAPI._session is None:

            client_id = client_id or os.environ.get('TOODLEDO_CLIENT_ID')
            client_secret = client_secret or os.environ.get('TOODLEDO_CLIENT_SECRET')
            ToodledoAPI._session = ToodledoAPI(session, cache, tasks_cache, client_id, client_secret, logger)
            if ToodledoAPI._session is not None:
                ToodledoAPI._session.update_cache()

        return ToodledoAPI._session

    @staticmethod
    def hide_password(msg):
        if msg:
            msg = re.sub('password=.*&', 'password=*****&', msg, re.IGNORECASE)
        return msg

    def __init__(self, session='~/.tdapi.oauth2', cache='~/.tdapi.cache', tasks_cache='~/.tdapi.tasks',
                 client_id=None, client_secret=None, logger=None):


# region Logging
        from pyutils import get_logger, LogAdapter
        if logger is None:
            self._logger = get_logger('tdapi', 'DEBUG')
        else:
            self._logger = logger
        self._adapter = LogAdapter(self._logger, {'package': 'tdapi', 'callback': ToodledoAPI.hide_password})
# endregion

        self._client_id = client_id or os.environ.get('TOODLEDO_CLIENT_ID')
        self._client_secret = client_secret or os.environ.get('TOODLEDO_CLIENT_SECRET')

        self._session = None
        self._session_file = None

        self._tasks_cache = None
        self._tasks_cache_file = None

        self._cache = None
        self._cache_file = None

        self._offline = None

        self._account = None
        self._folders = None
        self._contexts = None
        self._goals = None
        self._locations = None
        self._tasks = None

        for parm in ['session', 'cache', 'tasks_cache']:
            ref = eval(parm)
            if ref is not None:
                if isinstance(ref, dict):
                    self.__dict__['_' + parm] = ref
                else:
                    self.__dict__['_' + parm + '_file'] = ref
                    if os.path.isfile(os.path.expanduser(ref)):
                        with codecs.open(os.path.expanduser(ref), 'r', encoding='utf-8') as fh:
                            self.__dict__['_' + parm] = json.load(fh)

# region Default properties
    @property
    def logger(self):return self._adapter

    # @property
    # def authenticated(self): return self._access_token is not None

    @property
    def offline(self): return self._offline == True

    @property
    def online(self): return self._offline == False
# endregion

    @property
    def access_token(self):
        return self._session.get('access_token') if isinstance(self._session, dict) else None

    @property
    def refresh_token(self):
        return self._session.get('refresh_token') if isinstance(self._session, dict) else None

    @property
    def expired(self):
        return bool((int(time.time()) - self._session.get('time_stamp',0)) > self._session.get('expires_in', 0))

    @property
    def account(self):
        from tdapi import ToodledoAccount
        if self._account is None:
            self._account = ToodledoAccount(self._request('account', 'get'), self)
        return self._account

    @property
    def tasks(self):
        from tdapi import ToodledoTasks, ToodledoTask
        if self._tasks is None:
            if self._tasks_cache is None:
                self._update_tasks_cache()
            self._tasks = ToodledoTasks(self._tasks_cache, self)
        return self._tasks

    def _authorize(self):
        url = 'https://%s/account/authorize.php' % (ToodledoAPI._SERVICE_URL)
        params = {'response_type': 'code', 'client_id' : self._client_id, 'state': '569cc6ba091a1', 'scope': 'basic tasks notes'}
        # response = requests.get(url, params=params)

    def _refresh(self):
        url = 'https://%s:%s@%s/account/token.php' % (self._client_id, self._client_secret, ToodledoAPI._SERVICE_URL)
        data = {'grant_type': 'refresh_token', 'refresh_token': self.refresh_token}
        self._session = self._response(requests.post(url, data=data))
        if self._session is not None:
            self._session['time_stamp'] = int(time.time())
            self.logger.debug('Refresh: %s' % (self._session))
            with codecs.open(os.path.expanduser(self._session_file), 'w', encoding='utf-8') as fp:
                json.dump(self._session, fp, indent=4, ensure_ascii=False, encoding='utf-8')

    def _update_tasks_cache(self):

        from tdapi import ToodledoTasks, ToodledoTask
        data = self._request('tasks', 'get', params={'fields': ','.join(ToodledoTask.fields('all'))})
        if data is not None:
            self._tasks_cache = {'lastedit': self.account.lastedit_task, 'data': data[1:]}
            with codecs.open(os.path.expanduser(self._tasks_cache_file), 'w', encoding='utf-8') as fp:
                json.dump(self._tasks_cache, fp, indent=4, ensure_ascii=False, encoding='utf-8')

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

    def update_cache(self):

        if self._account is None:
            self._account = self.get_account_info()

        from tdapi import ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations
        for list in [ToodledoFolders, ToodledoContexts, ToodledoGoals, ToodledoLocations]:

            if self._cache is not None:
                if self._cache.get(list.MODULE):
                    if self._cache[list.MODULE].get('lastedit'):
                        if self._cache[list.MODULE]['lastedit'] >= self._account[list.LASTEDIT]:
                            self.__dict__['_' + list.MODULE] = list(self._cache[list.MODULE], self)
                            continue

            if self._cache is None: self._cache = {}
            if self._cache.get(list.MODULE) is None: self._cache[list.MODULE] = {}
            self._cache[list.MODULE]['data'] = self._request(list.MODULE, 'get')
            self._cache[list.MODULE]['lastedit'] = self._account[list.LASTEDIT]
            self.__dict__['_' + list.MODULE] = list(self._cache[list.MODULE], self)

        if self._cache_file is not None:
           with codecs.open(os.path.expanduser(self._cache_file), 'w', encoding='utf-8') as fp:
                json.dump(self._cache, fp, indent=4, ensure_ascii=False, encoding='utf-8')

    def get_account_info(self):
        from tdapi import ToodledoAccount
        return ToodledoAccount(self._request('account', 'get'), self)

    def get_folders(self):
        from tdapi import ToodledoFolders
        data = self._request('folders', 'get')
        return ToodledoFolders(data, self)

    def get_tasks(self, **kwargs):
        from tdapi import ToodledoTasks
        return ToodledoTasks(self._request('tasks', 'get', params=kwargs), self)

    def get_task(self, id, **kwargs):
        from tdapi import ToodledoTask
        kwargs['id'] = id
        #fields=ToodledoTask.fields('all')
        data = self._request('tasks', 'get', params=kwargs)
        return ToodledoTask(data[1], self)

    def delete_task(self, id):
        from tdapi import ToodledoTask
        task = self.get_task(id)
        task.delete()

    def create_task(self, task=None, **kwargs):

        return task
        pass

    def update_task(self, task):
        return task
        pass

# region __Main__

if __name__ == '__main__':

    from tdapi import *

    toodledo = ToodledoAPI.get_session()
    print toodledo.account.email

    exit(0)

    #account =  toodledo.get_account_info()
    #print account

    folders = toodledo.get_folders()
    for folder in folders:
        print folder

    task = toodledo.get_tasks(id=23774181, fields=ToodledoTask.fields('all'))[0]
    task = toodledo.get_task(23774181)

    # task.note = 'Task note'
    # task.tag = '[Tag]'
    # task.update()

    exit(0)

# endregion


