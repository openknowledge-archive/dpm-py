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
from ..base import BaseCliTestCase, jsonify


class TagSuccessTest(BaseCliTestCase):
    """
    When user tags a datapackage, and tag sting is valid, dpm should report sucess.
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
        # AND registry server accepts tagging of the datapackage
        responses.add(
            responses.POST, 'https://example.com/api/package/user/some-datapackage/tag',
            json={'message': 'OK'},
            status=200)

    def test_tag_success(self):
        # WHEN `dpm tag newtag` is invoked
        result = self.invoke(cli, ['tag', 'newtag'])

        # THEN 'Datapackage successfully tagged' should be printed to stdout
        self.assertRegexpMatches(result.output, 'Datapackage successfully tagged')
        # AND 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # POST tag datapackage
                ('POST', 'https://example.com/api/package/user/some-datapackage/tag',
                    {'version': 'newtag'})])
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
