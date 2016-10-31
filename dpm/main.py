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
@click.pass_context
def cli(ctx, configfile):
    config = ConfigObj(configfile)
    ctx.obj = config
    defaults = {
        'server': os.environ.get('DPM_SERVER') \
                  or config.get('server') \
                  or DEFAULT_SERVER,
        'username': os.environ.get('DPM_USERNAME') or config.get('username'),
        'password': os.environ.get('DPM_PASSWORD') or config.get('password')
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
@click.pass_context
def publish(ctx, username, password, server, publisher):
    """
    Publish datapackage to the registry server.
    """
    client.publish(ctx, username, password, server)
    click.echo('publish ok')


def get_credentials():
    """
    Get credentials to authenticate user for server. If cached credentials are invalid,
    generate new.

    :return:
        str -- Credentials string

    TODO: this is basically a stub. Should use real credentials format instead of email\password
    """
    if exists(credsfile) and not isfile(credsfile):
        # credentials file path is taken for dir or non-file. Exit.
        print(
            "Can't generate new credentials. %s should be a file."
            " Please remove it and try again." % credsfile)
        sys.exit(1)

    if not exists(credsfile):
        print('Please provide email and password you used to signup at data portal.')
        email = input('Your email: ')
        password = getpass('Your password: ')
        with open(credsfile, 'w+') as credsfileh:
            credsfileh.write('%s\n%s' % (email, password))

    credentials = open(credsfile).read()

    # TODO: check if credentials are valid?
    return credentials


if __name__ == '__main__':
    cli()
