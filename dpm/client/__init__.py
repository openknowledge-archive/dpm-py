# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json as json_module
import os
import os.path
from os.path import exists, isfile, join, getsize
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

        file_list = ['datapackage.json']

        accepted_readme = ['README', 'README.txt', 'README.md']
        files = filter(isfile, listdir(self.datapackage.base_path))
        readme_list = [f for f in files if f in accepted_readme]
        if readme_list:
            readme = readme_list[0]
            file_list.append(readme)

        for resource in self.datapackage.resources:
            file_list.append(resource.descriptor['path'])

        filedata = {}
        for file in file_list:
            filedata[file] = self._get_file_info(file)

        file_info_for_request = {
            'metadata': {
                'owner': self.username,
                'name': self.datapackage.descriptor['name']
            },
            'filedata': filedata
        }

        response = self._apirequest(
                method='POST',
                url='/api/datastore/authorize',
                json=file_info_for_request
            )
        filedata = response.json().get('filedata')
        if not filedata:
            raise DpmException('server did not provide upload authorization for files')

        # Upload datapackage.json
        for path in file_list:
            self._upload_file(path, filedata[path])

        # TODO: (?) echo('Finalizing ... ', nl=False)
        data_package_s3_url = filedata['datapackage.json']['upload_url'] + '/' +\
                              filedata['datapackage.json']['upload_query']['key']
        response = self._apirequest(
            method='POST',
            url='/api/package/upload',
            json={'datapackage': data_package_s3_url}
        )
        status = response.json().get('status', None)
        if status is None or status != 'queued':
            raise DpmException('server did not provide upload authorization for files')

        # Return published datapackage url
        return self.server + '/%s/%s' % (self.username, self.datapackage.descriptor['name'])

    def _get_file_info(self, path):
        local_path = join(self.datapackage.base_path, path)
        md5 = md5_file_chunk(local_path)
        size = getsize(local_path)

        file_type = 'binary/octet-stream'
        if path.endswith('.json'):
            file_type = 'application/json'

        return {
            'size': size,
            'md5': md5,
            'type': file_type,
            'name': path
        }

    def _upload_file(self, path, data):
        '''Upload a file within the data package.'''
        # TODO: (?) echo('Uploading resource %s' % resource.local_data_path)
        local_path = join(self.datapackage.base_path, path)
        filestream = open(local_path, 'rb')

        response = requests.post(data['upload_url'],
                                 data=data['upload_query'],
                                 files={'file': filestream})

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
            headers.setdefault('Auth-Token', '%s' % self.token)

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

    def tag(self, tag_string):
        """
        Tag datapackage on the registry server.
        """
        self._ensure_auth()
        response = self._apirequest(
            method='POST',
            url='/api/package/%s/%s/tag' % (self.username, self.datapackage.descriptor['name']),
            json={'version': tag_string})

    def purge(self):
        """
        Purge datapackage from the registry server.
        """
        # echo('Purging %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self._ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='/api/package/%s/%s/purge' % (self.username, self.datapackage.descriptor['name']))

    def delete(self):
        """
        Delete datapackage from the registry server.
        """
        # echo('Deleting %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self._ensure_auth()
        response = self._apirequest(
            method='DELETE',
            url='/api/package/%s/%s' % (self.username, self.datapackage.descriptor['name']))

    def undelete(self):
        """
        Undelete datapackage from the registry server.
        """
        # echo('Undeleting %s ... ' % dp.descriptor['name'], nl=False)  # TODO: logging
        self._ensure_auth()
        response = self._apirequest(
            method='POST',
            url='/api/package/%s/%s/undelete' % (self.username, self.datapackage.descriptor['name']))


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
    # report.pop('time')

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
        # table.pop('time')

        echo(json_module.dumps(table, indent=4), fg=color, bold=True)
        if errors:
            echo('---------', bold=True)
        for error in errors:
            error = {key: value or '-' for key, value in error.items()}
            echo('[{row-number},{column-number}] [{code}] {message}'.format(**error))
