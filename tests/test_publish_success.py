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
from .base import BaseCliTestCase, StringIO, jsonify


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
                    {"name": "some-resource", "path": "./data/some_data.csv", }
                ]
            },
            default_base_path='.')
        patch('dpm.client.DataPackage', lambda *a: self.valid_dp).start()
        patch('dpm.client.exists', lambda *a: True).start()

    @patch('dpm.client.filter', lambda *a: ['README.md'])
    @patch('dpm.utils.file.open', mock_open())  # mock csv file open
    @patch('dpm.utils.file.getsize', lambda a: 5)  # mock csv file size
    @patch('dpm.client.md5_file_chunk', lambda a:
           '855f938d67b52b5a7eb124320a21a139')  # mock md5 checksum
    def test_publish_success(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)
        # AND registry server accepts any datapackage
        responses.add(
            responses.PUT, 'https://example.com/api/package/user/some-datapackage',
            json={'message': 'OK'},
            status=200)
        # AND registry server gives bitstore upload url
        responses.add(
            responses.POST, 'https://example.com/api/auth/bitstore_upload',
            json={'key': 'https://s3.fake/put_here'},
            status=200)
        # AND s3 server allows data upload
        responses.add(
            responses.PUT, 'https://s3.fake/put_here',
            json={'message': 'OK'},
            status=200)
        # AND registry server successfully finalizes upload
        responses.add(
            responses.POST, 'https://example.com/api/package/user/some-datapackage/finalize',
            json={'message': 'OK'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN 'publish ok' should be printed to stdout
        self.assertRegexpMatches(result.output, 'publish ok')
        # AND 7 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "password"}),
                # PUT metadata with datapackage.json contents
                ('PUT', 'https://example.com/api/package/user/some-datapackage',
                    self.valid_dp.to_dict()),
                # POST authorize presigned url for s3 upload
                ('POST', 'https://example.com/api/auth/bitstore_upload',
                    {"publisher": "user", "package": "some-datapackage",
                     "path": "./data/some_data.csv", "md5": '855f938d67b52b5a7eb124320a21a139'}),
                # PUT data to s3
                ('PUT', 'https://s3.fake/put_here', ''),
                # POST authorized presigned url for README
                ('POST', 'https://example.com/api/auth/bitstore_upload',
                    {"publisher": "user", "package": "some-datapackage",
                     "path": "README.md", "md5": '855f938d67b52b5a7eb124320a21a139'}),
                # PUT README to S3
                ('PUT', 'https://s3.fake/put_here', ''),
                # POST finalize upload
                ('POST', 'https://example.com/api/package/user/some-datapackage/finalize', '')])
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
