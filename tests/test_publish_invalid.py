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
            "name": "some-name",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.datapackage', DataPackage=lambda *a: valid_dp).start()
        patch('dpm.main.exists', lambda *a: True).start()

        # AND valid credentials
        patch('dpm.main.get_credentials', lambda *a: 'fake creds').start()

    def test_publish_invalid(self):
        # GIVEN the server that rejects datapackage as invalid
        responses.add(
                responses.POST, 'https://example.com/api/v1/package',
                json={'error': 'invalid datapackage json', 'error_code': 'DP_INVALID'},
                status=400)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish'])

        # THEN exit code should be 1
        self.assertEqual(result.exit_code, 1)
        # AND 'datapackage.json is invalid' should be printed to stdout
        self.assertTrue('datapackage.json is invalid' in result.output)
