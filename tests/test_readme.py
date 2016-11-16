# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import builtins
import datapackage
import json
import responses
from mock import patch, mock_open, MagicMock
from six import string_types

from dpm.main import cli
from .base import BaseCliTestCase


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
        })
        patch('dpm.main.client.do_publish.validate',
              lambda *a: self.valid_dp).start()

    @patch('dpm.client.do_publish.filter', lambda a, b: ['README.md'])
    def test_readme_sucess_with_extension(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # Checking README
        self.assertNotIn('Publishing Package without README', result.output)

    @patch('dpm.client.do_publish.filter', lambda a, b: ['README'])
    def test_readme_sucess_without_extension(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # Checking README
        self.assertNotIn('Publishing Package without README', result.output)

    @patch('dpm.client.do_publish.filter', lambda a, b: ['README.'])
    def test_readme_warning_invalid_extension(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # Checking README
        self.assertIn('Publishing Package without README', result.output)

    @patch('dpm.client.do_publish.filter', lambda a, b: [])
    def test_readme_warning_for_noreadme(self):
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # Checking README
        self.assertIn('Publishing Package without README', result.output)
