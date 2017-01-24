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

import os
import sys
from functools import wraps
from os.path import exists, isfile

import click
import requests
from datapackage.exceptions import ValidationError

from .utils.click import echo
from . import config
from . import __version__
from . import client as dprclient


# Disable click warning. We are trying to be python3-compatible
# with unicode_literals.
click.disable_unicode_literals_warning = True


def echo_errors(f):
    """
    Decorator for subcommands, that will echo any known errors from Client.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except dprclient.ConfigError as e:
            echo('[ERROR]: %s \n\n'
                 'To enter configuration options please run:\n'
                 '    dpmpy configure\n' % str(e))
            sys.exit(1)
        except requests.ConnectionError as e:
            echo('[ERROR] %s\n' % repr(e))
            echo('Network error. Please check your connection settings\n')
            sys.exit(1)
        except dprclient.HTTPStatusError as e:
            echo('[ERROR] %s\n' % str(e.message))
            sys.exit(1)
        except dprclient.DpmException as e:
            echo('[ERROR] %s\n' % str(e))
            sys.exit(1)

    return wrapped


@click.group()
@click.version_option(version=__version__)
@click.option('--config', 'config_path',
              help='Use custom config file. Default %s' % config.configfile)
@click.option('--debug', is_flag=True, default=False,
              help='Show debug messages')
@click.pass_context
def cli(ctx, config_path, debug):
    if ctx.invoked_subcommand == 'configure':
        # configure does not require Client isntance.
        return

    # Create client instance to use in subcommands.
    try:
        client = dprclient.Client('.', config=config.read_config(config_path))
    except Exception as e:
        echo('[ERROR] %s\n' % str(e))
        sys.exit(1)

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

    try:
        client.validate()
    except (ValidationError, dprclient.ResourceDoesNotExist) as e:
        echo('[ERROR] %s\n' % str(e))
        sys.exit(1)

    echo('datapackage.json is valid\n')


@cli.command()
@echo_errors
def purge():
    """
    Purge datapackage from the registry server.
    """
    client = click.get_current_context().meta['client']
    client.purge()
    echo('purge ok')


@cli.command()
@echo_errors
def delete():
    """
    Delete datapackage from the registry server.
    """
    client = click.get_current_context().meta['client']
    client.delete()
    echo('delete ok')


@cli.command()
@echo_errors
def publish():
    """
    Publish datapackage to the registry server.
    """
    client = click.get_current_context().meta['client']
    puburl = client.publish()
    echo('Datapackage successfully published. It is available at %s' % puburl)


if __name__ == '__main__':
    cli()
