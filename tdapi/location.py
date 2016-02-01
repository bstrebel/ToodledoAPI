#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, re, requests
from tdapi import *

class ToodledoLocation(ToodledoBean):

    MAP = {'id': None, 'name': None, 'description': None, 'lat': None, 'lon': None}
    DEFAULT = map
    MODULE = 'locations'

    def __init__(self, data=None, tdapi=None, parent=None, **kwargs):
        ToodledoBean.__init__(self, data, tdapi, parent, **kwargs)

class ToodledoLocations(ToodledoBeans):

    ITEMS = ToodledoLocation
    MODULE = 'locations'
    LASTEDIT = 'lastedit_location'

    def __init__(self, data=None, tdapi=None):

        ToodledoBeans.__init__(self, ToodledoLocation, data, tdapi)
