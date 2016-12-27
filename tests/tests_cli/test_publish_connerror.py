# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import requests
from requests.exceptions import InvalidSchema, MissingSchema
import six
import unittest
from mock import patch

from dpm.main import cli
from ..base import BaseCliTestCase


class ConnectionErrorTest(BaseCliTestCase):
    """
    When connection error happens, dpm publish should report the error to the user.
    """
    mock_requests = False  # Use low-level socket mocks instead of requests lib mocks.

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

    def test_connerror_oserror(self):
        # GIVEN socket that throws OSError
        with patch("socket.socket.connect", side_effect=OSError) as mocksock:
            # WHEN dpm publish is invoked
            try:
                result = self.invoke(cli, ['publish', ])
            except Exception as e:
                result = e

            if six.PY2:
                # On python2 requests does not wrap the socket errors in
                # requests.ConnectionError. Dpm will not handle it in any way
                # THEN OSError should be raised
                assert isinstance(result, OSError)
            else:
                # python3
                # THEN 'Network error' should be printed to stdout
                self.assertRegexpMatches(result.output, 'Network error')
                # AND exit code should be 1
                self.assertEqual(result.exit_code, 1)

            # AND socket.connect should be called once with server address
            mocksock.assert_called_once_with(('example.com', 443))

    def test_connerror_ioerror(self):
        # GIVEN socket that throws IOError
        with patch("socket.socket.connect", side_effect=IOError) as mocksock:
            # WHEN dpm publish is invoked
            try:
                result = self.invoke(cli, ['publish', ])
            except Exception as e:
                result = e

            if six.PY2:
                # On python2 requests does not wrap the socket errors in
                # requests.ConnectionError. Dpm will not handle it in any way
                # THEN IOError should be raised
                assert isinstance(result, IOError)
            else:
                # python3
                # THEN 'Network error' should be printed to stdout
                self.assertRegexpMatches(result.output, 'Network error')
                # AND exit code should be 1
                self.assertEqual(result.exit_code, 1)

            # AND socket.connect should be called once with server address
            mocksock.assert_called_once_with(('example.com', 443))

    def test_connerror_typeerror(self):
        """
        Any unexpected error from socket should be propagated to the cli.
        """
        # GIVEN socket that throws TypeError
        with patch("socket.socket.connect", side_effect=TypeError) as mocksock:
            # WHEN dpm publish is invoked
            try:
                result = self.invoke(cli, ['publish', ])
            except Exception as e:
                result = e

            # THEN TypeError should be raised
            assert isinstance(result, TypeError)

    def test_connerror_invalid_url_schema(self):
        # GIVEN server url with invalid 'htt:' schema
        self.config['server'] = 'htt://127.0.0.1'

        # WHEN dpm publish is invoked
        try:
            result = self.invoke(cli, ['publish', ])
        except Exception as e:
            result = e

        # THEN InvalidSchema should be raised
        assert isinstance(result, InvalidSchema)
        # AND it should say that schema is invalid
        assert "No connection adapters were found for 'htt://127.0.0.1/api/auth/token'" in str(result)

    def test_connerror_missing_url_schema(self):
        # GIVEN server url with missing schema
        self.config['server'] = '127.0.0.1'

        # WHEN dpm publish is invoked
        try:
            result = self.invoke(cli, ['publish', ])
        except Exception as e:
            result = e

        # THEN MissingSchema should be raised
        assert isinstance(result, MissingSchema)
        # AND it should say that schema is invalid
        assert "Invalid URL '127.0.0.1/api/auth/token': No schema supplied. Perhaps you meant http://127.0.0.1/api/auth/token?" in str(result)
