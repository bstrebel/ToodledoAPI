#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
from tdapi import *

class ToodledoFolder(ToodledoBean):

    MAP = {'id': None, 'name': None, 'private': None, 'archived': None, 'ord': None}
    DEFAULT = map
    MODULE = 'folders'

    def __init__(self, data=None, tdapi=None, parent=None):

        ToodledoBean.__init__(self, data, tdapi, parent)

class ToodledoFolders(ToodledoBeans):

    ITEMS = ToodledoFolder
    MODULE = 'folders'
    LASTEDIT = 'lastedit_folder'

    def __init__(self, data=None, tdapi=None):

        ToodledoBeans.__init__(self, ToodledoFolder, data, tdapi)
