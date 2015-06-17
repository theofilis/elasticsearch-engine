#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

VERSION = (0, 1, 0)

__version__ = ".".join(map(str, VERSION[0:3])) + "".join(VERSION[3:])
__author__ = "George Theofilis"
__contact__ = "theofilis.g@gmail.com"
__homepage__ = "https://github.com/theofilis/elasticsearch-engine"

from django.conf import settings

if "elasticsearch_engine" not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS.insert(0, "elasticsearch_engine")