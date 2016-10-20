# -*- coding: utf-8 -*-
"""
Runtime variables like data directories, etc.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
from os.path import exists, join

from .utils.compat import expanduser


configdir = expanduser('~/.dpm')
if not exists(configdir):
    os.makedirs(configdir)

# The credentials file to authorize with datapackage registry server.
credsfile = join(configdir, 'creds.jwt')

# The config file in INI(ConfigObj) format.
configfile = join(configdir, 'config')

