# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import responses
from mock import patch
from configobj import ConfigObj
from mock import patch, MagicMock, Mock
from click.testing import CliRunner, Result

from dpm.main import cli
from .base import BaseCliTestCase, StringIO


class PublishAuthServerErrorTest(BaseCliTestCase):
    """
    When registry(auth) server returns empty auth token or empty bitstore put url, client should
    print error and exit.
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

    def test_getting_empty_auth_token(self):
        # GIVEN registry server that returns empty token
        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={"token": ""},
                status=200)
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN 'server did not return auth token' should be printed to stdout
        self.assertRegexpMatches(result.output, 'Server did not return auth token')
        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)

    @patch('dpm.client.md5_file_chunk', lambda a: '855f938d6')  # mock md5 checksum
    def test_getting_empty_put_url(self):
        # GIVEN registry server that accepts any user
        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={"token": "sometoken"},
                status=200)
        # AND registry server accepts any datapackage
        responses.add(
                responses.PUT, 'https://example.com/api/package/user/some-datapackage',
                json={'message': 'OK'},
                status=200)
        # AND registry server gives empty bitstore upload url
        responses.add(
                responses.POST, 'https://example.com/api/auth/bitstore_upload',
                json={'key': ""},
                status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN 'server did not return resource put url' should be printed to stdout
        self.assertRegexpMatches(result.output, 'server did not provide upload authorization for path:')
        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)
