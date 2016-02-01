#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
from tdapi import *

class ToodledoContext(ToodledoBean):

    MAP = {'id': None, 'name': None, 'private': None}
    DEFAULT = map
    MODULE = 'contexts'

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):
        ToodledoBean.__init__(self, data, tdapi, parent, **kwargs)

class ToodledoContexts(ToodledoBeans):

    ITEMS = ToodledoContext
    MODULE = 'contexts'
    LASTEDIT = 'lastedit_context'

    def __init__(self, data=None, tdapi=None):

        ToodledoBeans.__init__(self, ToodledoContext, data, tdapi)
