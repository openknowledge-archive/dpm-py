#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dpm is a package manager for datapackages.

Usage:
  dpm publish
  dpm validate

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os
import sys
from functools import wraps
from os.path import exists, isfile

import click
import datapackage
from requests.exceptions import ConnectionError

from . import __version__
from . import config
from . import dpmclient
from .utils.click import echo


# Disable click warning. We are trying to be python3-compatible
# with unicode_literals.
click.disable_unicode_literals_warning = True

def echo_errors(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except dpmclient.MissingCredentialsError:
            echo('[ERROR]: missing user credentials. \n\n'
                 'To enter your credentials please run:\n'
                 '    dpmpy configure\n')
            sys.exit(1)
        except (OSError, IOError, ConnectionError) as e:
            echo('[ERROR] %s\n' % repr(e))
            echo('Network error. Please check your connection settings\n')
            sys.exit(1)
        except dpmclient.ServerJsonError:
            echo('[ERROR] Invalid JSON response from server\n')
            sys.exit(1)
        except dpmclient.ServerError as e:
            echo('[ERROR] Server response: %s %s\n' % (
                    e.response.status_code,
                    (e.response.json().get('message') or e.response.json().get('description'))
            ))
            sys.exit(1)
        except (dpmclient.BitstoreAuthServerError, dpmclient.AuthServerError) as e:
            echo('[ERROR] %s\n' % e.message)
            sys.exit(1)
        #except Exception as e:
            #echo('[ERROR] %s' % repr(e))
            #sys.exit(1)

    return wrapped


@click.group()
@click.version_option(version=__version__)
@click.option('--config', 'config_path', default=config.configfile,
              help='Use custom config file. Default ~/.dpm/config')
@click.option('--debug', is_flag=True, default=False,
              help='Show debug messages')
@click.pass_context
def cli(ctx, config_path, debug):
    if not exists('datapackage.json'):
        echo('[ERROR] Current directory is not a datapackage: datapackage.json not found.\n')
        sys.exit(1)

    try:
        json.load(open('datapackage.json'))
    except Exception as e:
        # TODO: show more detailed error message - at least line number
        # See also: https://github.com/frictionlessdata/datapackage-py/issues/113
        echo('[ERROR] datapackage.json is malformed\n')
        sys.exit(1)

    client = dpmclient.Client(config=config.read_config(config_path))
    ctx.meta['client'] = client


@cli.command()
def configure():
    """
    Update configuration options. Configuration will be saved in ~/.dpm/conf or
    the file provided with --config option.
    """
    config.prompt_config(click.get_current_context().parent.params['config_path'])


@cli.command()
def validate():
    """
    Validate datapackage in the current dir. Print validation errors if found.
    """
    client = click.get_current_context().meta['client']
    dp = datapackage.DataPackage('datapackage.json')

    try:
        client.validate(dp)
    except datapackage.exceptions.ValidationError:
        echo('[ERROR] datapackage.json is invalid.\n')
        errors = list(dp.iter_errors())
        for n, error in enumerate(errors, 1):
            if len(errors) > 1:
                echo('Error %d ' % n, nl=False)
            # TODO: printing error looks very noisy on output, maybe try to make it look nice.
            # Printing first line is better, but still cryptic sometimes:
            # https://github.com/frictionlessdata/dpmpy/issues/15#issuecomment-257318423
            echo('%s\n' % str(error).split('\n')[0])
        sys.exit(1)
    except dpmclient.ResourceDoesNotExist as e:
        echo('[ERROR] resource does not exist:')
        for resource in e.resources:
            echo(' %s' % resource.local_data_path)
        echo('')
        sys.exit(1)

    echo('datapackage.json is valid\n')


@cli.command()
@echo_errors
def purge():
    """
    Purge datapackage from the registry server.
    """
    client = click.get_current_context().meta['client']
    dp = datapackage.DataPackage('datapackage.json')
    client.purge(dp)
    echo('purge ok')


@cli.command()
@echo_errors
def delete():
    """
    Delete datapackage from the registry server.
    """
    client = click.get_current_context().meta['client']
    dp = datapackage.DataPackage('datapackage.json')
    client.delete(dp)
    echo('delete ok')


@cli.command()
@echo_errors
def publish():
    """
    Publish datapackage to the registry server.
    """
    client = click.get_current_context().meta['client']
    dp = datapackage.DataPackage('datapackage.json')
    client.publish(dp)
    echo('publish ok')


if __name__ == '__main__':
    cli()
