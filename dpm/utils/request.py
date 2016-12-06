# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import os

import requests
from click import echo, secho
from requests.exceptions import ConnectionError


def request(method, *args, **kwargs):
    """
    General request-response processing routine for dpr-api server.
    Will raise SystemExit in case of common network/response errors.

    :return:
        Response -- requests.Response instance

    """
    methods = {
        'POST': requests.post,
        'PUT': requests.put,
        'GET': requests.get,
        'DELETE': requests.delete
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


def authenticate(server, username, password):
    """
    Get auth token from the server using credentials. Token can be used in future
    requests to the server.
    """
    if not (username and password):
        secho('Error', fg='red', nl=False)
        echo(': missing user credentials. \n\nTo enter your credentials please run:')
        echo('\n    dpmpy configure\n')
        sys.exit(1)

    echo('Authenticating ... ', nl=False)
    authresponse = request('POST', url='%s/api/auth/token' % server,
                           json={'username': username, 'secret': password})

    token = authresponse.json().get('token')
    if not token:
        secho('FAIL\n', fg='red')
        echo('Error: server did not return auth token\n')
        sys.exit(1)
    secho('ok', fg='green')

    return token
