# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import responses
from mock import patch

from dpm.main import cli
from ..base import BaseCliTestCase


class ConfigureSuccessTest(BaseCliTestCase):
    """
    When user launches `dpmpy configure` and provides valid values for inputs,
    configuration should be saved to disk.
    """

    def test_configure_success(self):
        # GIVEN valid inputs for options
        options = {
            'Username: ': 'user',
            'Your access_token (input hidden): ': 'access_token',
            'Server URL: ': 'http://example.com'
        }
        patch('dpm.config.input', lambda opt: options[opt]).start()
        patch('dpm.config.getpass', lambda opt: options[opt]).start()

        # WHEN `dpm configure` is invoked
        result = self.invoke(cli, ['configure'])

        # THEN 'Configuration saved' should be printed to stdout
        self.assertRegexpMatches(result.output, 'Configuration saved')
        # AND config should be written to disk
        self.config.write.assert_called_once()
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
