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


class PublishSuccessTest(BaseCliTestCase):
    """
    When user publishes valid datapackage, and server accepts it, dpm should
    report sucess.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client', validate=lambda *a: valid_dp).start()

        # AND valid credentials
        patch('dpm.main.get_credentials', lambda *a: 'fake creds').start()

    def test_publish_success(self):
        # GIVEN the server that accepts datapackage
        responses.add(
                responses.PUT, 'https://example.com/api/package/testpub/some-datapackage',
                json={'message': 'OK'},
                status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN exit code should be 0
        self.assertEqual(result.exit_code, 0)
        # AND 'publish OK' should be printed to stdout
        self.assertTrue('publish ok' in result.output)
