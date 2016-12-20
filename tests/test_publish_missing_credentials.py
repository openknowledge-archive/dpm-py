# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import responses
from mock import patch
from configobj import ConfigObj
from mock import patch, MagicMock, Mock
from click.testing import CliRunner, Result

from dpm.main import cli
from .base import BaseCliTestCase, StringIO


class PublishMissingCredentialsTest(BaseCliTestCase):
    """
    When user publishes datapackage, and the user credentials are missing in the config,
    error should be displayed.
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

    def test_missing_credentials(self):
        self._config = ConfigObj({
            'username': 'user',
        })
        self.config = MagicMock(spec_set=self._config)
        self.config.__getitem__.side_effect = self._config.__getitem__
        self.config.__setitem__.side_effect = self._config.__setitem__
        self.config.get.side_effect = self._config.get
        patch('dpm.config.ConfigObj', lambda *a: self.config).start()

        self.runner = CliRunner()
        result = self.invoke(cli, ['publish'])
        self.assertRegexpMatches(result.output, 'password is required')
