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
from .base import BaseCliTestCase


class PublishInvalidTest(BaseCliTestCase):
    """
    When user publishes datapackage, which is deemed invalid by server, the error message should
    be displayed.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client.do_publish.validate', lambda *a: valid_dp).start()

    def test_publish_invalid(self):
        # GIVEN the server that accepts any user
        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={'token': 'blabla'},
                status=200)
        # AND server rejects any datapackage as invalid
        responses.add(
                responses.PUT, 'https://example.com/api/package/user/some-datapackage',
                json={'message': 'invalid datapackage json'},
                status=400)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN 'datapackage.json is invalid' should be printed to stdout
        self.assertRegexpMatches(result.output, 'invalid datapackage json')
        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)

    def test_missing_credentials(self):
        #Testing Missing Credentials
        self._config = ConfigObj({
        'username': 'user',
        })
        self.config = MagicMock(spec_set=self._config)
        self.config.__getitem__.side_effect = self._config.__getitem__
        self.config.__setitem__.side_effect = self._config.__setitem__
        self.config.get.side_effect = self._config.get
        patch('dpm.main.ConfigObj', lambda *a: self.config).start()

        self.runner = CliRunner()
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])
        self.assertRegexpMatches(result.output, 'missing user credentials')

    def test_notify_token_not_received(self):
        #Testing token received
        # GIVEN the server that accepts any user
        self.valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client.do_publish.validate', lambda *a: self.valid_dp).start()

        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={"token":""},
                status=200)
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN 'datapackage.json is invalid' should be printed to stdout
        self.assertRegexpMatches(result.output, 'server did not return auth token')
        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)


    def test_notify_put_url_not_received(self):
        #Testing notificaion on put url
        # GIVEN the server that accepts any user
        self.valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client.do_publish.validate', lambda *a: self.valid_dp).start()

        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={"token":"sometoken"},
                status=200)
        # AND registry server accepts any datapackage
        responses.add(
                responses.PUT, 'https://example.com/api/package/user/some-datapackage',
                json={'message': 'OK'},
                status=200)
        # AND registry server gives bitstore upload url
        responses.add(
                responses.POST, 'https://example.com/api/auth/bitstore_upload',
                json={'key': ""},
                status=200)
        # AND s3 server allows data upload

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN 'datapackage.json is invalid' should be printed to stdout
        self.assertRegexpMatches(result.output, 'server did not return resource put url')
        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)
