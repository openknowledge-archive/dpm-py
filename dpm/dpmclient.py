# -*- coding: utf-8 -*-
"""
The client to work with dpr-api.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
from os.path import basename, exists, isfile, realpath

import requests
from requests.exceptions import ConnectionError
from click import echo, secho, progressbar

from .utils.md5_hash import md5_file_chunk
from .utils.file import ChunkReader


class AuthServerError(Exception):
    def __init__(self, message):
        self.message = message

class BitstoreAuthServerError(Exception):
    def __init__(self, message):
        self.message = message

class DatapackageJsonInvalidError(Exception):
    pass

class ServerError(Exception):
    def __init__(self, response):
        self.response = response

class ServerJsonError(Exception):
    pass

class MissingCredentialsError(Exception):
    pass

class ResourceDoesNotExist(Exception):
    def __init__(self, resources):
        self.resources = resources


class Client(object):
    def __init__(self, config):
        self.server = config['server']
        self.username = config['username']
        self.password = config['password']
        self.token = None

    def validate(self, datapackage):
        """
        Validate datapackage metadata.
        TODO: validate data https://github.com/frictionlessdata/dpm-py/issues/46
        """
        datapackage.validate()

        nonexisting = [x for x in datapackage.resources if not exists(x.local_data_path)]
        if nonexisting:
            raise ResourceDoesNotExist(nonexisting)

    def _apirequest(self, method, *args, **kwargs):
        """
        General request-response processing routine for dpr-api server.

        :return:
            Response -- requests.Response instance

        """
        methods = {
            'POST': requests.post,
            'PUT': requests.put,
            'GET': requests.get,
            'DELETE': requests.delete
        }

        headers = kwargs.pop('headers', {})
        if self.token:
            headers.setdefault('Authorization', 'Bearer %s' % self.token)

        response = methods.get(method)(*args, headers=headers, **kwargs)

        try:
            jsonresponse = response.json()
        except Exception as e:
            six.raise_from(ServerJsonError('Invalid JSON response from server'), e)

        if response.status_code not in (200, 201):
            raise ServerError(response)

        return response

    def ensure_auth(self):
        """
        Get auth token from the server using credentials. Token can be used in future
        requests to the server.
        # TODO: is this private or useful outside?
        # TODO: refresh expired token
        """
        if self.token:
            return self.token

        if not (self.username and self.password):
            raise MissingCredentialsError()

        #echo('Authenticating ... ', nl=False)  # TODO: logging
        authresponse = self._apirequest(
                method='POST',
                url='%s/api/auth/token' % self.server,
                json={'username': self.username, 'secret': self.password})

        self.token = authresponse.json().get('token')
        if not self.token:
            raise AuthServerError('Server did not return auth token')

        return self.token

    def _upload(self, package_name, filepath, click=None):
        """
        Get the presigned-put-url and upload file to the bitstore.
        """
        #echo('Uploading resource %s' % resource.local_data_path)  # TODO: logging

        # Ask the server for s3 put url for a file.
        response = self._apirequest(
                method='POST',
                url='%s/api/auth/bitstore_upload' % self.server,
                json={
                    'publisher': self.username,
                    'package': package_name,
                    'path': basename(filepath),
                    'md5': md5_file_chunk(filepath)
                },
                headers={'Authorization': 'Bearer %s' % self.token})
        puturl = response.json().get('key')
        if not puturl:
            raise BitstoreAuthServerError('Server did not return file put url')

        filestream = ChunkReader(filepath)

        # TODO: logging
        #if debug:
            #echo('Uploading to %s' % puturl)
            #echo('File size %d' % filestream.len)

        # TODO: subclassing the client may be saner approach than injecting click all
        # the way down here.
        if click:
            with click.progressbar(length=filestream.len, label=' ') as bar:
                filestream.on_progress = bar.update
                response = requests.put(puturl, data=filestream)
        else:
            response = requests.put(puturl, data=filestream)

    def publish(self, dp, click=None):
        """
        Publish datapackage with all resources and README.
        """
        self.ensure_auth()

        accepted_readme = ['README', 'README.txt', 'README.md']
        readme_list = [f for f in filter(isfile, os.listdir('.')) if f in accepted_readme]

        # TODO: logging
        #if not readme_list:
            #echo('Warning: Publishing Package without README', fg='yellow')

        #echo('Uploading datapackage.json ... ', nl=False)  # TODO: logging
        response = self._apirequest(
                method='PUT',
                url='%s/api/package/%s/%s' % (self.server, self.username, dp.descriptor['name']),
                json=dp.descriptor)

        for resource in dp.resources:
            self._upload(dp.descriptor['name'], resource.local_data_path, click)

        if readme_list:
            self._upload(dp.descriptor['name'], realpath(readme_list[0]), click)

        # Finalize publish to trigger server pick it up.
        #echo('Finalizing ... ', nl=False)  # TODO: logging
        response = self._apirequest(
            method='POST',
            url='%s/api/package/%s/%s/finalize' % (self.server, self.username, dp.descriptor['name']))

    def purge(self, dp):
        """
        Purge datapackage from the registry server.
        """
        #echo('Purging %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self.ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='%s/api/package/%s/%s/purge' % (self.server, self.username, dp.descriptor['name']))

    def delete(self, dp):
        """
        Delete datapackage from the registry server.
        """
        #echo('Deleting %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self.ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='%s/api/package/%s/%s' % (self.server, self.username, dp.descriptor['name']))


