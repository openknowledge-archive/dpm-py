# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import unittest
import datapackage
from mock import patch

from dpm.main import cli
from .base import BaseCliTestCase


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
            result = self.invoke(cli, ['publish', ])

            # THEN 'Network error' should be printed to stdout
            self.assertRegexpMatches(result.output, 'Network error')
            # AND socket.connect should be called once with server address
            mocksock.assert_called_once_with(('example.com', 443))
            # AND exit code should be 1
            self.assertEqual(result.exit_code, 1)

    def test_connerror_ioerror(self):
        # GIVEN socket that throws IOError
        with patch("socket.socket.connect", side_effect=IOError) as mocksock:
            # WHEN dpm publish is invoked
            result = self.invoke(cli, ['publish', ])

            # THEN 'Network error' should be printed to stdout
            self.assertRegexpMatches(result.output, 'Network error')
            # AND socket.connect should be called once with server address
            mocksock.assert_called_once_with(('example.com', 443))
            # AND exit code should be 1
            self.assertEqual(result.exit_code, 1)

    def test_connerror_typeerror(self):
        # GIVEN socket that throws TypeError
        with patch("socket.socket.connect", side_effect=TypeError) as mocksock:
            # WHEN dpm publish is invoked
            try:
                result = self.invoke(cli, ['publish', ])
            except Exception as e:
                result = e

            # THEN TypeError should be raised
            self.assertTrue(isinstance(result, TypeError))

    @patch("dpm.config.ConfigObj", lambda *a: {'server_url': 'http://127.0.0.1:1'})
    @unittest.skip
    def test_connerror_wrong_url(self):
        # NOTE: Error handling currently does not distinguish various local
        # connectivity issues from server connection issues (host unreachable or
        # closed port)
        # We can provide more informative messages to user by handling this
        # more gracefully, but there are challenges on py2/py3 compatibility
        # side. Namely different requests/urllib3 exception handling: under py2
        # it reraises OSError/IOError from socket unmodified, while under py3
        # it wraps it in custom exception classes.

        # WHEN dpm publish is invoked
        result = self.invoke(cli, ['publish'])

        self.assertTrue(isinstance(result, ConnectionError))
        # THEN exit code should be 1
        self.assertEqual(result.exit_code, 1)
        # AND 'Network error' should be printed to stdout
        self.assertRegexpMatches(result.output, 'Network error')
