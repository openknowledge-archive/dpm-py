from unittest import TestCase

import responses
from click.testing import CliRunner
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
    mock_requests = True  # Flag if the testcase should mock out requests library

    def _pre_setup(self):
        # Use Mocket to prevent any real network access from tests
        Mocket.enable()

        # Mock at the level of requests library.
        # Connectivity tests can use lower level mocks at socket level instead.
        if self.mock_requests:
            responses.start()

        # Start with empty config by default
        self.config = patch('dpm.main.config', {}).start()
        #self.config.update(
            #server_url='https://example.com'
        #)

        self.runner = CliRunner()

    def _post_teardown(self):
        """ Disable all mocks """
        if self.mock_requests:
            responses.stop()
        Mocket.disable()
        patch.stopall()

    def invoke(self, *args, **kwargs):
        """
        Wrapper around CliRunner.invoke() propagating exceptions by default.
        """
        kwargs.setdefault('catch_exceptions', False)
        return self.runner.invoke(*args, **kwargs)


