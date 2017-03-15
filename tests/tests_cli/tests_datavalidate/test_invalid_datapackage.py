# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json
from os.path import abspath
from textwrap import dedent

import datapackage
from mock import patch, MagicMock

from dpm.main import cli
from dpm.client import Client
from ...base import BaseCliTestCase


class DatavalidateInvalidDatapackageTest(BaseCliTestCase):
    """
    When user launches `datavalidate` inside a datapackage dir, and one of the datapackage resource
    files has data with invalid schema, then validation error should be printed to stdout.
    """

    def setUp(self):
        # GIVEN datapackage with one resource
        invalid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                {
                    "path": "invalid.csv",
                    "schema": {
                        "fields": [
                            {
                                "name": "Price", "type": "number"
                            },
                            {
                                # Column 2 name should be "Year"
                                "name": "Year", "type": "date", "format": "%Y"
                            }
                        ]
                    }
                }
            ]},
            default_base_path='.')
        patch('dpm.main.exists', lambda *a: True).start()
        patch('dpm.main.DataPackage', lambda *a: invalid_dp).start()

        # AND the resource file has invalid schema (column 2 name should be 'Year')
        with open('invalid.csv', 'w') as f:
            f.write(
                'Price,Ugh\n'  # 'Ugh' != 'Year'
                '1,1980'
            )

    def test_validate_invalid_datapackage_human_report(self):
        # WHEN `dpm datavalidate` is invoked
        result = self.invoke(cli, ['datavalidate'])

        # THEN error should be printed to the output
        assert "Header in column 2 doesn't match field name Year" in result.output

        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)

    def test_validate_invalid_datapackage_json(self):
        # WHEN `dpm datavalidate --json` is invoked
        result = self.invoke(cli, ['datavalidate', '--json'])

        report = json.loads(result.output)

        # Strip time measurements
        # https://github.com/frictionlessdata/goodtables-py/issues/169
        report.pop('time')
        report['errors'] = []
        for table in report['tables']:
            table.pop('time')

        # THEN json with validation error should be printed to stdout
        assert report == {
            "valid": False,
            "table-count": 1,
            "errors": [],
            "tables": [
                {
                    "row-count": 2,
                    "headers": [
                        "Price",
                        "Ugh"
                    ],
                    "errors": [
                        {
                            "code": "non-matching-header",
                            "row-number": None,
                            "message": "Header in column 2 doesn't match field name Year",
                            "row": None,
                            "column-number": 2
                        }
                    ],
                    "error-count": 1,
                    "valid": False,
                    "source": abspath("invalid.csv")
                }
            ],
            "error-count": 1
        }

        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)
