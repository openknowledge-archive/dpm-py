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
from dpm.utils.md5_hash import md5_file_chunk
from dpm.utils.request import request, authenticate
from dpm.utils.file import ChunkReader

from .do_validate import validate


def publish(ctx, username, password, server, debug):
    """
    Publish datapackage to the registry server.
    """
    dp = validate()
    token = authenticate(server, username, password)

    accepted_readme = ['README', 'README.txt', 'README.md']
    readme_list = [f for f in filter(isfile, os.listdir('.'))
                   if f in accepted_readme]

    if not readme_list:
        secho('Warning: Publishing Package without README', fg='yellow')

    echo('Uploading datapackage.json ... ', nl=False)
    response = request(
            method='PUT',
            url='%s/api/package/%s/%s' % (server, username, dp.descriptor['name']),
            json=dp.descriptor,
            headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')

    for resource in dp.resources:
        echo('Uploading resource %s' % resource.local_data_path)

        # Ask the server for s3 put url for a resource.
        response = request(
                method='POST',
                url='%s/api/auth/bitstore_upload' % server,
                json={
                    'publisher': username,
                    'package': dp.descriptor['name'],
                    'path': basename(resource.local_data_path),
                    'md5': md5_file_chunk(resource.local_data_path)
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
        response = request(
                method='POST',
                url='%s/api/auth/bitstore_upload' % server,
                json={
                    'publisher': username,
                    'package': dp.descriptor['name'],
                    'path': basename(readme_local_path),
                    'md5': md5_file_chunk(readme_local_path)
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
    response = request(
        method='POST',
        url='%s/api/package/%s/%s/finalize' % (server, username, dp.descriptor['name']),
        headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')

