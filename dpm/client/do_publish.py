# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys

import requests
from requests.exceptions import ConnectionError
from click import echo, secho
from .do_validate import validate


def publish(ctx, username, password, server):
    """
    Publish datapackage to the registry server.
    """
    dp = validate()

    if not (username and password):
        secho('Error', fg='red', nl=False)
        echo(': missing user credentials. \nTo enter your credentials please run:')
        echo('\n    dpmpy configure\n')
        sys.exit(1)

    echo('Authenicating ... ', nl=False)
    authresponse = request('POST', url='%s/api/auth/token' % server,
                           json={'username': username, 'secret': password})

    token = authresponse.json().get('token')
    if not token:
        secho('FAIL', fg='red')
        echo('Error: server did not return auth token', color='red')
        sys.exit(1)
    secho('ok', fg='green')

    echo('Uploading datapackage.json ... ', nl=False)
    response = request('PUT',
        '%s/api/package/%s/%s' % (server, username, dp.descriptor['name']),
        json=dp.descriptor,
        headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')


def request(method, *args, **kwargs):
    methods = {'POST': requests.post, 'PUT': requests.put}

    try:
        response = methods.get(method)(*args, **kwargs)
    except (OSError, IOError, ConnectionError) as e:
        secho('FAIL', fg='red')
        echo('Original error was: %s' % repr(e))
        echo('Network error. Please check your connection settings')
        sys.exit(1)

    try:
        jsonresponse = response.json()
    except Exception as e:
        secho('FAIL', fg='red')
        echo('Original error was: %s' % repr(e))
        echo('Invalid JSON response from server')
        sys.exit(1)

    if response.status_code not in (200, 201):
        secho('FAIL', fg='red')
        echo('Server response: %s %s' % (
            response.status_code,
            (jsonresponse.get('message') or jsonresponse.get('description'))
        ))
        sys.exit(1)

    return response
