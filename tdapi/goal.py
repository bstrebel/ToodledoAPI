#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
from tdapi import *

class ToodledoGoal(ToodledoBean):

    MAP = {'id': None, 'name': None, 'level': None, 'archived': None, 'contributes': None, 'note': None}
    DEFAULT = map
    MODULE = 'goals'

    LEVELS = {'lifetime': 0,
              'long-term': 1,
              'short-term': 2}

    DEFAULT_LEVEL = 2

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):
        ToodledoBean.__init__(self, data, tdapi, parent, **kwargs)
        if self.level is None:
            self.level = self.DEFAULT_LEVEL

class ToodledoGoals(ToodledoBeans):

    ITEMS = ToodledoGoal
    MODULE = 'goals'
    LASTEDIT = 'lastedit_goal'

    def __init__(self, data=None, tdapi=None):

        ToodledoBeans.__init__(self, ToodledoGoal, data, tdapi)
