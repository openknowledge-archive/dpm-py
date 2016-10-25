# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
from unittest import TestCase

import responses
from click.testing import CliRunner, Result
from mock import patch
from mocket.mocket import Mocket


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


class BaseCliTestCase(SimpleTestCase):
    mock_requests = True  # Flag if the testcase should mock out requests library.
    isolate = True  # Falg if the test should run in isolated environment.

    def _pre_setup(self):
        # Use Mocket to prevent any real network access from tests
        Mocket.enable()

        # Mock at the level of requests library.
        # Connectivity tests can use lower level mocks at socket level instead.
        if self.mock_requests:
            responses.start()

        # Start with empty config by default
        #patch('dpm.main.ConfigObj', lambda *a: {}).start()
        self.config = {
            'username': 'user',
            'pasword': 'password',
        }
        patch('dpm.main.ConfigObj', lambda *a: self.config).start()
        #self.config.update(
            #server_url='https://example.com'
        #)

        self.runner = CliRunner()

    def _post_teardown(self):
        """ Disable all mocks """
        if self.mock_requests:
            responses.stop()
        # TODO: Mocket.disable() sometimes makes tests hang.
        #Mocket.disable()
        patch.stopall()

    def invoke(self, cli, args=None, **kwargs):
        """
        Invoke click command. If self.isolate is True, then delegate to
        self.runner.invoke(), which will create isolated environment.
        Otherwise invoke command directly, which should allow to use debugger.
        The issue is that debuggers are confused by click wrappers in
        place of sys.stdin and sys.stdout
        """
        kwargs.setdefault('catch_exceptions', False)
        if self.isolate:
            result = self.runner.invoke(cli, args, **kwargs)
        else:
            exit_code = 0
            exception = None
            exc_info = None
            try:
                cli.main(args=args, prog_name=cli.name or 'root')
            except SystemExit as e:
                exit_code = e.code
            result = Result(runner=self.runner,
                            output_bytes=b'',
                            exit_code=exit_code,
                            exception=exception,
                            exc_info=exc_info)
        return result


