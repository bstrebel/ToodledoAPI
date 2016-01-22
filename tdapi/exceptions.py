#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, json, re, requests

class ToodledoRequestError(Exception):

    def __init__(self, error):
        self._error = error
        self._message = 'Toodledo request error [%s]: %s' % (self._error.get('errorCode'), self._error.get('errorDesc'))

    def __repr__(self):
        return self._message

    def __str__(self):
        return self._message


class ToodledoError(Exception):

    def __init__(self, error):
        self._error = error
        self._message = 'Toodledo error [%s]: %s' % (self._error.get('errorCode'), self._error.get('errorDesc'))

    def __repr__(self):
        return self._message

    def __str__(self):
        return self._message

