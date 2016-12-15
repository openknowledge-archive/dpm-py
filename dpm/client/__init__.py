from .do_configure import configure
from .do_delete import delete, purge
from .do_publish import publish
from .do_validate import validate

import os

import datapackage
import requests
import six


class DpmException(Exception):
    pass

class NetworkError(Exception):
    """ There was a connection error during request. """
    pass

class AuthError(Exception):
    """ Recieved malformed response form authentication server. """
    pass

class ConfigError(Exception):
    """ The configuration passed to the client is malformed. """
    pass

class JSONDecodeError(Exception):
    """ Failed to decode responce JSON. """
    def __init__(self, request, message):
        self.request = request
        self.message = message

class HTTPStatusError(Exception):
    """ Response status_code indicated error processing the request. """
    def __init__(self, request, message):
        self.request = request
        self.message = message


class MissingCredentialsError(Exception):
    pass


class Client(object):

    def __init__(self, config, data_package_path='', click=None):
        if not data_package_path:
            data_package_path = os.getcwd()
        data_package_path = os.path.abspath(data_package_path)
        # may want to use the datapackage-py here
        self.datapackage = self._load_dp(data_package_path)

        try:
            self.server = config['server']
            self.username = config['username']
            self.password = config['password']
        except KeyError as e:
            raise ConfigError('Configuration error: %s is required' % str(e))

        self.click = click
        self.token = None

    def _load_dp(self, path):
        dppath = os.path.join(path, 'datapackage.json')

        # do we need to do this or is it done in datapackage library?
        if not os.path.exists(dppath):
            raise DpmException('No Data Package found at %s. Did not find datapackage.json at %s' % (path, dppath))

        dp = datapackage.DataPackage(dppath)
        return dp

    def validate(self):
        self.datapackage.validate()

        # should we really check this here? Good question i think ...
        for idx, resource in enumerate(self.datapackage.resources):
            if not exists(resource.local_data_path):
                raise DpmException('Resource at index %s with name %s and path %s does not exist on disk' % (
                    idx, resource.name, resource.local_data_path)
                    )

        return True

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
            raise MissingCredentialsError('User credentials are missing.')

        #echo('Authenticating ... ', nl=False)  # TODO: logging
        authresponse = self._apirequest(
                method='POST',
                url='%s/api/auth/token' % self.server,
                json={'username': self.username, 'secret': self.password})

        self.token = authresponse.json().get('token')
        if not self.token:
            raise AuthError('Server did not return auth token')

        return self.token

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
            response.json()
        except Exception as e:
            six.raise_from(
                JSONDecodeError(response, message='Failed to decode JSON response from server'), e)

        if response.status_code not in (200, 201):
            raise HTTPStatusError(response, message='Error %s' % response.status_code)

        return response

