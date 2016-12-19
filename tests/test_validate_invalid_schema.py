# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
from mock import patch, MagicMock

from dpm.main import cli
from dpm.client import Client
from .base import BaseCliTestCase


class ValidateInvalidSchemaTest(BaseCliTestCase):
    """
    When user launches `validate` and datapackage.json schema is invalid, error message
    should be displayed.
    """

    def test_validate_invalid_schema(self):
        # GIVEN datapackage with invalid schema (missing resource path)
        invalid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource",}
            ]
        })
        patch('dpm.client.os.path.exists', lambda *a: True).start()
        patch('dpm.client.DataPackage', lambda *a: invalid_dp).start()

        # WHEN `dpm validate` is invoked
        result = self.invoke(cli, ['validate'])

        # AND validation error should be printed to stdout
        self.assertRegexpMatches(result.output, 'is not valid under any of the given schemas')
        # THEN exit code should be 1
        self.assertEqual(result.exit_code, 1)
