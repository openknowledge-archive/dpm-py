# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import builtins
import datapackage
import json
import responses
from mock import patch, mock_open
from six import string_types

from dpm.main import cli
from .base import BaseCliTestCase


def jsonify(data):
    if not data:
        return ''
    if isinstance(data, bytes):
        return json.loads(data.decode('utf8'))
    if not isinstance(data, string_types):
        return data.read(100)
    return json.loads(data)


class DeletePurgeSuccessTest(BaseCliTestCase):
    """
    When user deletes or purges datapackage, dpm should report sucess.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
                "name": "some-datapackage",
                "resources": [
                    {"name": "some-resource", "path": "./data/some_data.csv", }
                ]
            },
            default_base_path='.')
        patch('dpm.client.DataPackage', lambda *a: self.valid_dp).start()
        patch('dpm.client.exists', lambda *a: True).start()

        # AND the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)
        # AND registry server accepts deletion of any datapackage
        responses.add(
            responses.DELETE, 'https://example.com/api/package/user/some-datapackage',
            json={'message': 'OK'},
            status=200)
        # AND registry server accepts purging of any datapackage
        responses.add(
            responses.DELETE, 'https://example.com/api/package/user/some-datapackage/purge',
            json={'message': 'OK'},
            status=200)

    def test_delete_success(self):
        # WHEN `dpm delete` is invoked
        result = self.invoke(cli, ['delete'])

        # THEN 'delete ok' should be printed to stdout
        self.assertRegexpMatches(result.output, 'delete ok')
        # AND 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # DELETE datapackage
                ('DELETE', 'https://example.com/api/package/user/some-datapackage', '')])
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)

    def test_purge_success(self):
        # WHEN `dpm purge` is invoked
        result = self.invoke(cli, ['purge'])

        # THEN 'purge ok' should be printed to stdout
        self.assertRegexpMatches(result.output, 'purge ok')
        # AND 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # DELETE datapackage
                ('DELETE', 'https://example.com/api/package/user/some-datapackage/purge', '')])
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
