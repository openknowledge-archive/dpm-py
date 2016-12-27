# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
from unittest import TestCase
import json

import responses
import six
from configobj import ConfigObj
from click.testing import CliRunner, Result
from mock import patch, MagicMock, Mock

from . import mock_socket

# Disable network during tests
mock_socket.patch_socket()


if six.PY2:
    from cStringIO import StringIO
else:
    from io import TextIOWrapper, BytesIO, StringIO


def jsonify(data):
    """
    Convert response data to canonical form, used in tests for assertions.
    """
    if not data:
        return ''
    if isinstance(data, bytes):
        return json.loads(data.decode('utf8'))
    if not isinstance(data, six.string_types):
        # If data is not a string, it could be a file-like object returned by
        # `responses` library. We will return first 100 bytes.
        return data.read(100)
    return json.loads(data)


class SimpleTestCase(TestCase):
    """
    Taken from https://github.com/django/django/tree/master/django/test/tescases.py
    """
    def __call__(self, result=None):
        """
        Wrapper around default __call__ method to perform common test
        set up. This means that user-defined Test Cases aren't required to
        include a call to super().setUp().
        """
        testMethod = getattr(self, self._testMethodName)
        skipped = (getattr(self.__class__, "__unittest_skip__", False) or
            getattr(testMethod, "__unittest_skip__", False))

        if not skipped:
            try:
                self._pre_setup()
            except Exception:
                result.addError(self, sys.exc_info())
                return
        super(SimpleTestCase, self).__call__(result)
        if not skipped:
            try:
                self._post_teardown()
            except Exception:
                result.addError(self, sys.exc_info())
                return

    def _pre_setup(self):
        pass

    def _post_teardown(self):
        pass


class BaseTestCase(SimpleTestCase):
    mock_requests = True  # Flag if the testcase should mock out requests library.

    def _pre_setup(self):
        # Use Mocket to prevent any real network access from tests
        #Mocket.enable()

        # Mock at the level of requests library.
        # Connectivity tests can use lower level mocks at socket level instead.
        if self.mock_requests:
            responses.start()

    def _post_teardown(self):
        """
        Disable all mocks after the test.
        """
        if self.mock_requests:
            responses.reset()
            responses.stop()
        patch.stopall()


class BaseCliTestCase(BaseTestCase):
    isolate = False  # Flag if the test should run in isolated environment.

    def _pre_setup(self):
        super(BaseCliTestCase, self)._pre_setup()

        # Start with default config
        self._config = ConfigObj({
            'username': 'user',
            'access_token': 'access_token',
        })
        self.config = MagicMock(spec_set=self._config)
        self.config.__getitem__.side_effect = self._config.__getitem__
        self.config.__setitem__.side_effect = self._config.__setitem__
        self.config.get.side_effect = self._config.get
        patch('dpm.config.ConfigObj', lambda *a: self.config).start()

        self.runner = CliRunner()


    def invoke(self, cli, args=None, **kwargs):
        """
        Invoke click command. If self.isolate is True, then delegate to
        self.runner.invoke(), which will create isolated environment.
        Otherwise invoke command directly, which should allow to use debugger.
        The issue is that debuggers are confused by click wrappers in
        place of sys.stdin and sys.stdout
        """
        kwargs.setdefault('catch_exceptions', False)
        with self.runner.isolated_filesystem():
            if self.isolate:
                result = self.runner.invoke(cli, args, **kwargs)
            else:
                if six.PY2:
                    stdout = stderr = bytes_output = StringIO()
                else:
                    bytes_output = BytesIO()
                    stdout = stderr = TextIOWrapper(bytes_output, encoding='utf-8')

                patch('click.utils._default_text_stdout', lambda: stdout).start()
                patch('click.utils._default_text_stderr', lambda: stderr).start()
                exit_code = 0
                exception = None
                exc_info = None
                try:
                    cli.main(args=args, prog_name=cli.name or 'root')
                except SystemExit as e:
                    exit_code = e.code
                result = Result(runner=self.runner,
                                output_bytes=bytes_output.getvalue(),
                                exit_code=exit_code,
                                exception=exception,
                                exc_info=exc_info)
        return result
