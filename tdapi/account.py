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

        # create bean class map by data
        if data is not None:
            for key in data:
                ToodledoAccount.MAP[key] = True

        ToodledoBean.__init__(self, data, tdapi)
