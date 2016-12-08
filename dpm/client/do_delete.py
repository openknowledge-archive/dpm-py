# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys

from click import echo, secho
from dpm.utils.request import request, authenticate


from .do_validate import validate


def purge(ctx, username, password, server, debug):
    """
    Purge datapackage from the registry server.
    """
    dp = validate()
    token = authenticate(server, username, password)

    echo('Purging %s ... ' % dp.descriptor['name'], nl=False)
    response = request(
        method='DELETE',
        url='%s/api/package/%s/%s/purge' % (server, username, dp.descriptor['name']),
        headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')


def delete(ctx, username, password, server, debug):
    """
    Delete datapackage from the registry server.
    """
    dp = validate()
    token = authenticate(server, username, password)

    echo('Deleting %s ... ' % dp.descriptor['name'], nl=False)
    response = request(
        method='DELETE',
        url='%s/api/package/%s/%s' % (server, username, dp.descriptor['name']),
        headers={'Authorization': 'Bearer %s' % token})
    secho('ok', fg='green')
