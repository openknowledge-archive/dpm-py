# -*- coding: utf-8 -*-
"""
Configuration file reading/writing utils and defaults.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
from os.path import exists, join
from builtins import input

from configobj import ConfigObj
from getpass import getpass
from .utils.compat import expanduser


configdir = expanduser('~/.dpm')
if not exists(configdir):
    os.makedirs(configdir)

# The config file in INI(ConfigObj) format.
configfile = join(configdir, 'config')


# TODO: should we have hardcoded server default? Or always require user to enter?
DEFAULT_SERVER = 'https://example.com'


def prompt_config(config_path):
    """
    Ask user to enter config variables and then save it to disk.
    """
    from .utils.click import echo
	
    config = ConfigObj(config_path)

    echo('Please enter your username to authenticate '
        'for the datapackage registry server.')
    while True:
        config['username'] = input('Username: ')
        if config['username']:
            break
        else:
            echo('\nUsername should not be empty.')

    echo('\nPlease enter your access_token to authenticate '
          'for the datapackage registry server.')
    while True:
        config['access_token'] = getpass('Your access_token (input hidden): ')
        if config['access_token']:
            break
        else:
            echo('\naccess_token should not be empty.')

    echo('\nPlease enter registry server url. '
          'Leave blank to use default value: %s' % DEFAULT_SERVER)
    config['server'] = input('Server URL: ')

    config.write()
    echo('Configuration saved to: %s' % config.filename)


def read_config(config_path=None):
    """
    Read configuration from file, falling back to env or hardcoded defaults.
    """
    # this test comes first before we default config_path to default location
    # because we only care if config_path does not exist if user supplied it
    # (not if using default location - it is ok for that not to exist)
    if config_path is not None and not os.path.exists(config_path):
        raise Exception('No config file found at: %s' % config_path)
    if config_path is None:
        config_path = configfile
    config = ConfigObj(config_path)
    return  {
        'server': os.environ.get('DPM_SERVER') \
                  or config.get('server') \
                  or DEFAULT_SERVER,
        'username': os.environ.get('DPM_USERNAME') or config.get('username'),
        'access_token': os.environ.get('DPM_ACCESS_TOKEN') or config.get('access_token')
    }

