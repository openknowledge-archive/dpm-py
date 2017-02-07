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


class DatavalidateInvalidInferredSchemaTest(BaseCliTestCase):
    """
    When user launches `datavalidate` on standalone csv file with invalid schema, the
    schema should be inferred and validation error should be printed.
    """

    def setUp(self):
        # GIVEN csv file with invalid schema (non-integer value)
        with open('invalid.csv', 'w') as f:
            f.write(
                'Price,Year\n'
                '10,1980\n'
                '20,1981\n'
                'E,1982'  # non-integer value 'E' in col 1
            )

    def test_validate_invalid_inferred_schema_human_report(self):
        # WHEN `dpm datavalidate invalid.csv` is invoked
        result = self.invoke(cli, ['datavalidate', 'invalid.csv'])

        # THEN error should be printed
        assert "Row 4 has non castable value E in column 1" in result.output

        # AND exit code should be 1
        self.assertEqual(result.exit_code, 1)


    def test_validate_invalid_inferred_schema_json(self):
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
                    "headers": ["Price", "Year"],
                    "error-count": 1,
                    "errors": [
                        {
                            "message": "Row 4 has non castable value E in column 1 (type: integer, format: default)",
                            "code": "non-castable-value",
                            "row-number": 4,
                            "column-number": 1,
                            "row": [
                                "E",
                                "1982"
                            ]
                        }
                    ],
                    "row-count": 4,
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
