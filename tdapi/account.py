#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, json, re, requests
from tdapi import *


class ToodledoAccount(ToodledoBean):

    MAP = {}
    DEFAULT = map

    KEY = 'userid'
    NAME = 'email'

    def __init__(self, data=None, tdapi=None):

        # create bean class map by data returned
        if data is not None:
            for key,value in data.iteritems():
                default = None
                if isinstance(value, unicode):
                    default = u''
                elif isinstance(value, str):
                    default = ''
                else:
                    default = 0
                ToodledoAccount.MAP[key] = {'default': default, 'type': type(value), 'used': True}

        ToodledoBean.__init__(self, data, tdapi)
