# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import json
from mock import patch, MagicMock
from textwrap import dedent

from dpm.main import cli
from dpm.client import Client
from ...base import BaseCliTestCase


class DatavalidateInvalidStaticSchemaTest(BaseCliTestCase):
    """
    When user launches `datavalidate` on csv resource with invalid schema, according to the
    datapackage, then validation error should be printed to stdout.
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
            ]
        })
        patch('dpm.main.exists', lambda *a: True).start()
        patch('dpm.main.DataPackage', lambda *a: invalid_dp).start()

        # AND the resource file has invalid schema (column 2 name should be 'Year')
        with open('invalid.csv', 'w') as f:
            f.write(
                'Price,Ugh\n'  # 'Ugh' != 'Year'
                '1,1980'
            )

    def test_validate_invalid_static_schema_human_report(self):
        # WHEN `dpm datavalidate invalid.csv` is invoked
        result = self.invoke(cli, ['datavalidate', 'invalid.csv'])

        # THEN error should be printed to the output
        assert "Header in column 2 doesn't match field name Year" in result.output

        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)

    def test_validate_invalid_static_schema_json(self):
        # WHEN `dpm datavalidate invalid.csv --json` is invoked
        result = self.invoke(cli, ['datavalidate', 'invalid.csv', '--json'])

        report = json.loads(result.output)

        # Strip time measurements
        # https://github.com/frictionlessdata/goodtables-py/issues/169
        report.pop('time')
        for table in report['tables']:
            table.pop('time')

        # THEN json with validation error should be printed to stdout
        assert report == {
            "tables": [
                {
                    "headers": ["Price", "Ugh"],
                    "error-count": 1,
                    "errors": [
                        {
                            "message": "Header in column 2 doesn't match field name Year",
                            "code": "non-matching-header",
                            "row-number": None,
                            "column-number": 2,
                            "row": None
                        }
                    ],
                    "row-count": 2,
                    "valid": False,
                    "source": "invalid.csv"
                }
            ],
            "errors": [],
            "table-count": 1,
            "error-count": 1,
            "valid": False,
        }

        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)
