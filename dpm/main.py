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
from os.path import exists, isfile

import click
from configobj import ConfigObj
from .constants import DEFAULT_SERVER
from .runtime import credsfile, configfile
from . import __version__
from . import client


# Disable click warning. We are trying to be python3-compatible
# with unicode_literals.
click.disable_unicode_literals_warning = True


@click.group()
@click.version_option(version=__version__)
@click.option('--config', 'configfile', default=configfile,
              help='Use custom config file. Default ~/.dpm/config')
@click.option('--debug', is_flag=True, default=False)
@click.pass_context
def cli(ctx, configfile, debug):
    config = ConfigObj(configfile)
    ctx.obj = config
    defaults = {
        'server': os.environ.get('DPM_SERVER') \
                  or config.get('server') \
                  or DEFAULT_SERVER,
        'username': os.environ.get('DPM_USERNAME') or config.get('username'),
        'password': os.environ.get('DPM_PASSWORD') or config.get('password'),
        'debug': debug
    }
    ctx.default_map = {
        'publish': defaults,
        'configure': defaults,
    }


@cli.command()
@click.pass_context
def configure(ctx, **kwargs):
    """
    Update configuration options. Configuration will be saved in ~/.dpm/conf or
    the file provided with --config option.
    """
    config = ctx.obj
    client.configure(config)


@cli.command()
def validate():
    """
    Validate datapackage in the current dir. Print validation errors if found.
    """
    client.validate()
    click.echo('datapackage.json is valid')


@cli.command()
@click.option('--username')
@click.option('--password')
@click.option('--server')
@click.option('--publisher')
@click.option('--debug', is_flag=True)
@click.pass_context
def publish(ctx, username, password, server, publisher, debug):
    """
    Publish datapackage to the registry server.
    """
    client.publish(ctx, username, password, server, debug)
    click.echo('publish ok')


if __name__ == '__main__':
    cli()
