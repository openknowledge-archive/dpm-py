# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import builtins
import datapackage
import responses
from mock import patch, mock_open

from dpm.main import cli
from .base import BaseCliTestCase


class PublishSuccessTest(BaseCliTestCase):
    """
    When user publishes valid datapackage, and server accepts it, dpm should
    report sucess.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client.do_publish.validate', lambda *a: self.valid_dp).start()

        # AND valid credentials
        patch('dpm.main.get_credentials', lambda *a: 'fake creds').start()

    @patch('dpm.client.do_publish.open', mock_open())
    @patch('dpm.client.do_publish.getsize', lambda a: 5)
    def test_publish_success(self):
        # GIVEN the registry server that accepts any user
        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={'token': 'blabla'},
                status=200)
        # AND registry server gives bitstore upload url
        responses.add(
                responses.POST, 'https://example.com/api/auth/bitstore_upload',
                json={'key': 'https://s3.fake/put_here'},
                status=200)
        # AND registry server accepts any datapackage
        responses.add(
                responses.PUT, 'https://example.com/api/package/user/some-datapackage',
                json={'message': 'OK'},
                status=200)
        # AND s3 server allows data upload
        responses.add(
                responses.PUT, 'https://s3.fake/put_here',
                json={'message': 'OK'},
                status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN 'publish ok' should be printed to stdout
        self.assertRegexpMatches(result.output, 'publish ok')
        # AND POST(auth), PUT(metadata), POST(s3url) and PUT(data) requests should be sent
        self.assertEqual([x.request.method for x in responses.calls],
                         ['POST', 'PUT', 'POST', 'PUT'])
        # AND PUT request should contain serialized datapackage metadata
        self.assertEqual(responses.calls[1].request.body.decode(), self.valid_dp.to_json())
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
