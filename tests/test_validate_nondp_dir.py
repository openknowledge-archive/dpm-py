# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from dpm.main import cli
from .base import BaseCliTestCase


class ValidateNonDatapackageDirTest(BaseCliTestCase):
    """
    When user launches `validate` and datapackage.json is not found, error message
    should be displayed.
    """

    def test_validate_empty_dir(self):
        # GIVEN empty current dir
        with self.runner.isolated_filesystem():
            # WHEN `dpm validate` is invoked
            result = self.invoke(cli, ['validate'])

            # THEN 'Did not find datapackage.json' should be printed to stdout
            self.assertRegexpMatches(result.output, 'Did not find datapackage.json')
            # AND exit code should be 1
            self.assertEqual(result.exit_code, 1)
