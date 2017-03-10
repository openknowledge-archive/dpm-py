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
from ..base import BaseCliTestCase, StringIO, jsonify


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

    @patch('dpm.client.filter', lambda *a: ['README.md', 'datapackage.json'])
    @patch('dpm.client.open', mock_open())  # mock csv file open
    @patch('dpm.utils.file.getsize', lambda a: 5)  # mock csv file size
    @patch('dpm.client.getsize', lambda a: 10)  # mock all file size
    @patch('dpm.client.md5_file_chunk', lambda a:
           '855f938d67b52b5a7eb124320a21a139')  # mock md5 checksum
    def test_publish_success(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # AND registry server gives bitstore upload url
        responses.add(
            responses.POST, 'https://example.com/api/datastore/authorize',
            json={
                'filedata': {
                    'datapackage.json': {'upload_url': 'https://s3.fake/put_here_datapackege',
                                         'upload_query': {'key': 'k'}},
                    'README.md': {'upload_url': 'https://s3.fake/put_here_readme',
                                  'upload_query': {'key': 'k'}},
                    './data/some_data.csv': {'upload_url': 'https://s3.fake/put_here_resource',
                                             'upload_query': {'key': 'k'}}
                }
            },
            status=200)

        # AND s3 server allows data upload for datapackage
        responses.add(
            responses.POST, 'https://s3.fake/put_here_datapackege',
            json={'message': 'OK'},
            status=200)
        # AND s3 server allows data upload for readme
        responses.add(
            responses.POST, 'https://s3.fake/put_here_readme',
            json={'message': 'OK'},
            status=200)
        # AND s3 server allows data upload for resource
        responses.add(
            responses.POST, 'https://s3.fake/put_here_resource',
            json={'message': 'OK'},
            status=200)
        # AND registry server successfully finalizes upload
        responses.add(
            responses.POST, 'https://example.com/api/package/upload',
            json={'status': 'queued'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN published package url should be printed to stdout
        self.assertRegexpMatches(result.output, 'Datapackage successfully published. It is available at https://example.com/user/some-datapackage')
        # AND 6 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url)
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token'),

                # POST authorize presigned url for s3 upload
                ('POST', 'https://example.com/api/datastore/authorize'),
                # POST data to s3
                ('POST', 'https://s3.fake/put_here_datapackege'),
                ('POST', 'https://s3.fake/put_here_readme'),
                ('POST', 'https://s3.fake/put_here_resource'),
                # POST finalize upload
                ('POST', 'https://example.com/api/package/upload')
            ])
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
