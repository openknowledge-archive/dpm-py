# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import sys
from builtins import input
from getpass import getpass

from ..constants import DEFAULT_SERVER


def configure(config):
    """
    Update configuration options and save the config object to disk.
    """
    print('Please enter your username to authenticate '
        'for the datapackage registry server.')
    while True:
        config['username'] = input('Username: ')
        if re.match('^[a-zA-Z0-9_]+$', config['username']):
            break
        else:
            print('\nPlease enter valid username.')

    print('\nPlease enter your password to authenticate '
          'for the datapackage registry server.')
    while True:
        config['password'] = getpass('Your password: ')
        if config['password']:
            break
        else:
            print('\nPassword should not be empty.')

    print('\nPlease enter registry server url. '
          'Leave blank to use default value: %s' % DEFAULT_SERVER)
    config['server'] = input('Server URL: ')
    config.write()
