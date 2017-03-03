# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import unittest

import builtins
import datapackage
import json
import responses
from mock import patch, mock_open, MagicMock

from dpm.main import cli
from ..base import BaseCliTestCase, StringIO


class ReadmeTest(BaseCliTestCase):
    """
    Testcase for the Readme information.
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


    @unittest.skip("TODO: logging")
    @patch('dpm.client.filter', lambda a, b: ['README.md'])
    def test_readme_sucess_with_extension(self):
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # Checking README
        self.assertNotIn('Publishing Package without README', result.output)

    @unittest.skip("TODO: logging")
    @patch('dpm.client.filter', lambda a, b: ['README'])
    def test_readme_sucess_without_extension(self):
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # Checking README
        self.assertNotIn('Publishing Package without README', result.output)

    @unittest.skip("TODO: logging")
    @patch('dpm.client.filter', lambda a, b: ['README.'])
    def test_readme_warning_invalid_extension(self):
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # Checking README
        self.assertIn('Publishing Package without README', result.output)

    @unittest.skip("TODO: logging")
    @patch('dpm.client.filter', lambda a, b: [])
    def test_readme_warning_for_noreadme(self):
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # Checking README
        self.assertIn('Publishing Package without README', result.output)

    @patch('dpm.client.filter',
           lambda a, b: ['README.', 'README.txt', 'README.md', 'README', 'datapackage.json'])
    @patch('dpm.client.open', mock_open())  # mock csv file open
    @patch('dpm.utils.file.getsize', lambda a: 5)  # mock csv file size
    @patch('dpm.client.getsize', lambda a: 10)
    @patch('dpm.client.md5_file_chunk', lambda a:
           '855f938d67b52b5a7eb124320a21a139')  # mock md5 checksum
    def test_readme_sucess_for_multiple_readme(self):

        # Registry server gives bitstore upload urls
        responses.add(
            responses.POST, 'https://example.com/api/datastore/authorize',
            json={
                'filedata': {
                    'datapackage.json': {'upload_url': 'https://s3.fake/put_here_datapackege', 'upload_query': {}},
                    'README.txt': {'upload_url': 'https://s3.fake/put_here_readme', 'upload_query': {}},
                    './data/some_data.csv': {'upload_url': 'https://s3.fake/put_here_resource', 'upload_query': {}}
                }
            },
            status=200)
        # AND s3 server allows data upload for resource
        responses.add(
            responses.POST, 'https://s3.fake/put_here_resource',
            json={'message': 'OK'},
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

        # AND registry server successfully finalizes upload
        responses.add(
            responses.POST, 'https://example.com/api/package/upload',
            json={'status': 'queued'},
            status=200)
        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN published package url should be printed to stdout
        self.assertRegexpMatches(result.output, 'Datapackage successfully published. It is available at https://example.com/user/some-datapackage')

        # TODO: logging
        # Checking README uploading first match
        #self.assertNotIn('Publishing Package without README', result.output)
        #self.assertIn('Uploading README.txt', result.output)
