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
from .base import BaseCliTestCase, jsonify


class PublishReadFileErrorTest(BaseCliTestCase):
    """
    When user publishes datapackage, and read file error occurs, it should be propagated to
    the cli.
    """

    def test_publish_file_read_error(self):
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
        # AND registry server accepts any datapackage
        responses.add(
            responses.PUT, 'https://example.com/api/package/user/some-datapackage',
            json={'message': 'OK'},
            status=200)

        # AND the file that raises OSError on read()
        mockopen = patch('dpm.utils.md5_hash.open', mock_open()).start()
        mockopen.return_value.read.side_effect = OSError

        # WHEN `dpm publish` is invoked
        try:
            result = self.invoke(cli, ['publish'])
        except Exception as e:
            result = e

        # THEN OSError should be raised
        assert isinstance(result, OSError)
