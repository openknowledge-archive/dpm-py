# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import responses
from mock import patch

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

        # AND valid credentials
        patch('dpm.main.get_credentials', lambda *a: 'fake creds').start()

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
