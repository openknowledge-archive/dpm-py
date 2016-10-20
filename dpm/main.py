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

import sys
from builtins import input
from getpass import getpass
from os.path import exists, isfile

import click
import datapackage
import requests
from configobj import ConfigObj
from requests.exceptions import ConnectionError
from .runtime import credsfile, config


# Disable click warning. We are trying to be python3-compatible
# with unicode_literals.
click.disable_unicode_literals_warning = True

@click.group()
@click.version_option(version='0.1')
def cli():
    pass


@cli.command()
def validate():
    """
    Validate datapackage in the current dir. Print validation errors if found.
    """
    if not exists('datapackage.json'):
        print('Current directory is not a datapackage: datapackage.json not found.')
        sys.exit(1)

    try:
        dp = datapackage.DataPackage('datapackage.json')
    except:
        print('datapackage.json is malformed')
        sys.exit(1)

    try:
        dp.validate()
    except datapackage.exceptions.ValidationError:
        for error in dp.iter_errors():
            # TODO: printing error looks very noisy on output, maybe try make it look nice.
            print(error)
        sys.exit(1)

    print('datapackage.json is valid')
    return dp


@cli.command()
@click.pass_context
def publish(ctx):
    dp = ctx.invoke(validate)
    credentials = get_credentials()
    server_url = config.get('server_url', 'https://example.com')

    try:
        response = requests.post(
            '%s/api/v1/package' % server_url,
            json=dp.to_dict(),
            allow_redirects=True)
    except (OSError, IOError, ConnectionError) as e:
        # NOTE: This handling currently does not distinguish various local
        # connectivity issues from server connection issues (host unreachable or
        # closed port)
        # We can provide more informative messages to user by handling this
        # more gracefully, but there are challenges on py2/py3 compatibility
        # side. Namely different requests/urllib3 exception handling: under py2
        # it reraises OSError/IOError from socket unmodified, while under py3
        # it wraps it in custom exception classes.
        print('Original error was: %s' % repr(e))
        print('Network error. Please check your connection settings')
        sys.exit(1)

    if response.json():
        if response.json().get('error_code') == 'DP_INVALID':
            print('datapackage.json is invalid')
            sys.exit(1)
    print(response.status_code)

    print('publish ok')


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
