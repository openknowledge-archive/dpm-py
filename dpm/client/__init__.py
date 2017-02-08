# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json as json_module
import os
import os.path
from os.path import exists, isfile, join
from os import listdir

from builtins import filter
from datapackage import DataPackage
import goodtables
import requests
import six

from dpm.utils.md5_hash import md5_file_chunk
from dpm.utils.file import ChunkReader
from dpm.utils.click import echo


class DpmException(Exception):
    pass


class BaseResponseError(DpmException):
    """ Base class for errors caused by processing a response """
    def __init__(self, response, message):
        self.response = response
        self.message = message

    def __str__(self):
        return self.message

class AuthResponseError(BaseResponseError):
    """ Recieved malformed response form authentication server. """
    pass

class JSONDecodeError(BaseResponseError):
    """ Failed to decode response JSON. """
    pass

class HTTPStatusError(BaseResponseError):
    """ Response status_code indicated error processing the request. """
    pass


class ConfigError(DpmException):
    """ The configuration passed to the client is malformed. """
    pass


class ResourceDoesNotExist(DpmException):
    pass


class DataValidationError(DpmException):
    pass


class Client(object):

    def __init__(self, data_package_path='', config=None, click=None, datavalidate=False):
        if not data_package_path:
            data_package_path = os.getcwd()
        data_package_path = os.path.abspath(data_package_path)
        # may want to use the datapackage-py here
        self.datapackage = self._load_dp(data_package_path)

        self.click = click
        self.token = None
        self.config = config
        self.datavalidate = datavalidate

    def _ensure_config(self):
        try:
            self.server = self.config['server']
            self.username = self.config['username']
            self.access_token = self.config['access_token']
        except KeyError as e:
            raise ConfigError('Configuration error: %s is required' % str(e))

        for option in ('server', 'username', 'access_token'):
            if not self.config.get(option):
                raise ConfigError('Configuration error: %s is required' % option)

        if self.server.endswith('/'):
            # remove trailing slash
            self.server = self.server[:-1]

    def _load_dp(self, path):
        dppath = join(path, 'datapackage.json')

        # do we need to do this or is it done in datapackage library?
        if not exists(dppath):
            raise DpmException(
                'No Data Package found at %s. Did not find datapackage.json at %s' % (path, dppath))

        dp = DataPackage(dppath)
        return dp

    def validate(self):
        validate_metadata(self.datapackage)

        if self.datavalidate:
            report = validate_data(self.datapackage)
            if not report['valid']:
                print_inspection_report(report)
                raise DataValidationError('[ERROR] data validation failed!')
        return True

    def publish(self, publisher=None):
        """
        Publish datapackage to the registry server.

        @param publisher: optional publisher to use. If not provided
        first try to use publisher in datapackage.json and if that is missing
        use username.
        """
        self.validate()
        token = self._ensure_auth()

        # TODO: (?) echo('Uploading datapackage.json ... ', nl=False)
        response = self._apirequest(
                method='PUT',
                url='/api/package/%s/%s' % (self.username, self.datapackage.descriptor['name']),
                json=self.datapackage.descriptor
                )

        for resource in self.datapackage.resources:
            self._upload_file(resource.descriptor['path'], resource.local_data_path)

        files = filter(isfile, listdir(self.datapackage.base_path))
        accepted_readme = ['README', 'README.txt', 'README.md']
        readme_list = [f for f in files if f in accepted_readme]
        if readme_list:
            readme = readme_list[0]
            readme_local_path = join(self.datapackage.base_path, readme)
            self._upload_file(readme, readme_local_path)

        # TODO: (?) echo('Finalizing ... ', nl=False)
        response = self._apirequest(
            method='POST',
            url='/api/package/%s/%s/finalize' % (self.username, self.datapackage.descriptor['name'])
        )

        # Return published datapackage url
        return self.server + '/%s/%s' % (self.username, self.datapackage.descriptor['name'])

    def _upload_file(self, path, local_path):
        '''Upload a file within the data package.'''
        # TODO: (?) echo('Uploading resource %s' % resource.local_data_path)

        md5 = md5_file_chunk(local_path)
        # Ask the server for s3 put url for a resource.
        response = self._apirequest(
                method='POST',
                url='/api/auth/bitstore_upload',
                json={
                    'publisher': self.username,
                    'package': self.datapackage.descriptor['name'],
                    'path': path, 
                    'md5': md5 
                })
        data = response.json().get('data')

        if not data:
            raise DpmException('server did not provide upload authorization for path: %s' % path)

        # TODO: read file in chunks
        #filestream = ChunkReader(local_path)
        filestream = open(local_path, 'rb')

        # with progressbar(length=filestream.len, label=' ') as bar:
        #    filestream.on_progress = bar.update
        #    response = requests.put(puturl, data=filestream)
        response = requests.post(data['url'], data=data['fields'], files={'file': filestream})

        if response.status_code not in (200, 201, 204):
            raise HTTPStatusError(
                response,
                message='Bitstore upload failed.\nError %s\n%s' % (response.status_code, response.content))

    def _ensure_auth(self):
        """
        Get auth token from the server using credentials. Token can be used in future
        requests to the server.

        # TODO: refresh expired token
        """
        if self.token:
            return self.token
        
        self._ensure_config()
        authresponse = self._apirequest(
                method='POST',
                url='/api/auth/token',
                json={'username': self.username, 'secret': self.access_token})

        self.token = authresponse.json().get('token')
        if not self.token:
            raise AuthResponseError(authresponse, 'Server did not return auth token')

        return self.token

    def _apirequest(self, method, url, *args, **kwargs):
        """
        General request-response processing routine for dpr-api server.

        :return:
            Response -- requests.Response instance

        """

        # TODO: doing this for every request is kinda awkward
        self._ensure_config()

        if not url.startswith('http'):
            # Relative url is given. Build absolute server url
            url = self.server + url

        methods = {
            'POST': requests.post,
            'PUT': requests.put,
            'GET': requests.get,
            'DELETE': requests.delete
        }

        headers = kwargs.pop('headers', {})
        if self.token:
            headers.setdefault('Authorization', 'Bearer %s' % self.token)

        response = methods.get(method)(url, *args, headers=headers, **kwargs)

        try:
            jsonresponse = response.json()
        except Exception as e:
            six.raise_from(
                JSONDecodeError(response, message='Failed to decode JSON response from server'), e)

        if response.status_code not in (200, 201):
            raise HTTPStatusError(response, message='Error %s\n%s' % (
                response.status_code,
                jsonresponse.get('message') or jsonresponse.get('description')))

        return response

    def purge(self):
        """
        Purge datapackage from the registry server.
        """
        #echo('Purging %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self._ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='/api/package/%s/%s/purge' % (self.username, self.datapackage.descriptor['name']))

    def delete(self):
        """
        Delete datapackage from the registry server.
        """
        #echo('Deleting %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self._ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='/api/package/%s/%s' % (self.username, self.datapackage.descriptor['name']))


def validate_metadata(datapackage):
    datapackage.validate()

    # should we really check this here? Good question i think ...
    for idx, resource in enumerate(datapackage.resources):
        if not exists(resource.local_data_path):
            raise ResourceDoesNotExist(
                    'Resource at index %s and path %s does not exist on disk' % (
                    idx, resource.local_data_path)
                )

    return True


def validate_data(datapackage):
    inspector = goodtables.Inspector()
    return inspector.inspect(datapackage.descriptor, preset='datapackage')


def print_inspection_report(report, print_json=False):
    """
    Taken from https://github.com/frictionlessdata/goodtables-py/blob/master/goodtables/cli.py

    Print human-readable report from goodtables json report.
    """
    if print_json:
        return echo(json_module.dumps(report, indent=4))
    color = 'green' if report['valid'] else 'red'
    tables = report.pop('tables')
    errors = report.pop('errors')

    # TODO: time varies in tests, maybe we can omit it for simplicity
    # https://github.com/frictionlessdata/goodtables-py/issues/169
    #report.pop('time')

    echo('DATASET', bold=True)
    echo('=======', bold=True)
    echo(json_module.dumps(report), fg=color, bold=True)

    if errors:
        echo('---------', bold=True)
    for error in errors:
        error = {key: value or '-' for key, value in error.items()}
        echo('[{row-number},{column-number}] [{code}] {message}'.format(**error))
    for table_number, table in enumerate(tables, start=1):
        echo('\nTABLE [%s]' % table_number, bold=True)
        echo('=========', bold=True)
        color = 'green' if table['valid'] else 'red'
        errors = table.pop('errors')

        # TODO: time varies in tests, maybe we can omit it for simplicity
        #table.pop('time')

        echo(json_module.dumps(table, indent=4), fg=color, bold=True)
        if errors:
            echo('---------', bold=True)
        for error in errors:
            error = {key: value or '-' for key, value in error.items()}
            echo('[{row-number},{column-number}] [{code}] {message}'.format(**error))
