#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
from tdapi import *

class ToodledoGoal(ToodledoBean):

    MAP = {'id': None, 'name': None, 'level': None, 'archived': None, 'contributes': None, 'note': None}
    DEFAULT = map
    MODULE = 'goals'

    def __init__(self, data=None, tdapi=None, parent=None):

        ToodledoBean.__init__(self, data, tdapi, parent)

class ToodledoGoals(ToodledoBeans):

    ITEMS = ToodledoGoal
    MODULE = 'goals'
    LASTEDIT = 'lastedit_goal'

    def __init__(self, data=None, tdapi=None):

        ToodledoBeans.__init__(self, ToodledoGoal, data, tdapi)
