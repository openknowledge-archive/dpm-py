# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import re
import os
from builtins import open
from os.path import basename, getsize, realpath, isfile

import requests
from requests.exceptions import ConnectionError
from click import echo, secho, progressbar
from .do_validate import validate


def publish(ctx, username, password, server, debug):
    """
    Publish datapackage to the registry server.
    """
    dp = validate()

    if not (username and password):
        secho('Error', fg='red', nl=False)
        echo(': missing user credentials. \n\nTo enter your credentials please run:')
        echo('\n    dpmpy configure\n')
        sys.exit(1)

    echo('Authenicating ... ', nl=False)
    authresponse = request('POST', url='%s/api/auth/token' % server,
                           json={'username': username, 'secret': password})

    token = authresponse.json().get('token')
    if not token:
        secho('FAIL\n', fg='red')
        echo('Error: server did not return auth token\n')
        sys.exit(1)
    secho('ok', fg='green')

    accepted_readme = ['README', 'README.txt', 'README.md']
    readme_list = [f for f in filter(isfile, os.listdir('.'))
                   if f in accepted_readme]

    if not readme_list:
        secho('Warning: Publishing Package without README', fg='yellow')

    echo('Uploading datapackage.json ... ', nl=False)
    response = request('PUT',
                       '%s/api/package/%s/%s' % (server,
                                                 username, dp.descriptor['name']),
                       json=dp.descriptor,
                       headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')

    for resource in dp.resources:
        echo('Uploading resource %s' % resource.local_data_path)

        # Ask the server for s3 put url for a resource.
        response = request('POST',
                           '%s/api/auth/bitstore_upload' % (server),
                           json={
                               'publisher': username,
                               'package': dp.descriptor['name'],
                               'path': basename(resource.local_data_path)
                           },
                           headers={'Authorization': 'Bearer %s' % token})
        puturl = response.json().get('key')
        if not puturl:
            secho('ERROR ', fg='red', nl=False)
            echo('server did not return resource put url\n')
            sys.exit(1)

        filestream = ChunkReader(resource.local_data_path)

        if debug:
            echo('Uploading to %s' % puturl)
            echo('File size %d' % filestream.len)

        with progressbar(length=filestream.len, label=' ') as bar:
            filestream.on_progress = bar.update
            response = requests.put(puturl, data=filestream)

    if readme_list:
        readme_local_path = realpath(readme_list[0])
        echo('Uploading %s' % basename(readme_local_path))
        # Ask the server for s3 put url for a resource.
        response = request('POST',
                           '%s/api/auth/bitstore_upload' % (server),
                           json={
                               'publisher': username,
                               'package': dp.descriptor['name'],
                               'path': basename(readme_local_path)
                           },
                           headers={'Authorization': 'Bearer %s' % token})
        puturl = response.json().get('key')
        if not puturl:
            secho('ERROR ', fg='red', nl=False)
            echo('server did not return resource put url\n')
            sys.exit(1)

        filestream = ChunkReader(readme_local_path)

        if debug:
            echo('Uploading to %s' % puturl)
            echo('File size %d' % filestream.len)

        with progressbar(length=filestream.len, label=' ') as bar:
            filestream.on_progress = bar.update
            response = requests.put(puturl, data=filestream, headers={
                                    'Content-Length': '%d' % filestream.len})

    echo('Finalizing ... ', nl=False)
    response = request('POST',
                       '%s/api/package/%s/%s/finalize' % (
                           server, username, dp.descriptor['name']),
                       headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')


def request(method, *args, **kwargs):
    methods = {
        'POST': requests.post,
        'PUT': requests.put,
        'GET': requests.get
    }

    try:
        response = methods.get(method)(*args, **kwargs)
    except (OSError, IOError, ConnectionError) as e:
        secho('FAIL\n', fg='red')
        echo('Original error was: %s\n' % repr(e))
        echo('Network error. Please check your connection settings\n')
        sys.exit(1)

    try:
        jsonresponse = response.json()
    except Exception as e:
        secho('FAIL\n', fg='red')
        echo('Invalid JSON response from server\n')
        sys.exit(1)

    if response.status_code not in (200, 201):
        secho('FAIL\n', fg='red')
        echo('Server response: %s %s\n' % (
            response.status_code,
            (jsonresponse.get('message') or jsonresponse.get('description'))
        ))
        sys.exit(1)

    return response


class ChunkReader(object):
    """
    Chunked file reader. Implements file read api with ability to
    report read progress to specified callback.

    Usage:
        filestream = ChunkReader('/path/file.csv')
        with click.progressbar(length=filestream.len, label=' ') as bar:
            filestream.on_progress = bar.update
            response = requests.put(url, data=filestream)
    """
    on_progress = None

    def __init__(self, path):
        self.len = getsize(path)
        self._file = open(path, 'rb')

    def read(self, size):
        if self.on_progress:
            self.on_progress(128 * 1024)
        return self._file.read(128 * 1024)
