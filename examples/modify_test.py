import unittest
from modify import Modify

class HelpersTestCase(unittest.TestCase):
    def setUp(self):
        self.to_modify = Modify()

    def test_modify_date_format(self):
        expected = "any"
        dp = {'resources': [{"schema": {"fields": [{"name": "test","type": "date"}]}}]}
        datapackage = self.to_modify.transform_package(dp)
        result = datapackage['resources'][0]['schema']['fields'][0]['format']
        self.assertEqual(result, expected)

    def test_modify_date_format_works_with_multiple_date_fields(self):
        expected = "any"
        dp = {
            'resources': [{
            "schema": {"fields": [
                {"name": "test","type": "date"},
                {"name": "another-test","type": "date", "format": 'YYYY'}
                ]}
            }]
        }
        datapackage = self.to_modify.transform_package(dp)
        result_1 = datapackage['resources'][0]['schema']['fields'][0]['format']
        result_2 = datapackage['resources'][0]['schema']['fields'][1]['format']
        self.assertEqual(result_1, expected)
        self.assertEqual(result_2, expected)

    def test_modify_date_format_works_if_format_is_wrong(self):
        expected = "any"
        dp = {
            'resources': [{
            "schema": {"fields": [{"name": "test","type": "date", "format": 'YYYY'}]}
            }]
        }
        datapackage = self.to_modify.transform_package(dp)
        result = datapackage['resources'][0]['schema']['fields'][0]['format']
        self.assertEqual(result, expected)

    def test_transform_works_if_number_type_is_wrong(self):
        expected = 'number'
        dp = {'resources': [{"schema": {"fields": [{"name": "test","type": "decimal"}]}}]}
        datapackage = self.to_modify.transform_package(dp)
        result = datapackage['resources'][0]['schema']['fields'][0]['type']
        self.assertEqual(result, expected)

        dp = {'resources': [{"schema": {"fields": [{"name": "test","type": "float"}]}}]}
        datapackage = self.to_modify.transform_package(dp)
        result = datapackage['resources'][0]['schema']['fields'][0]['type']
        self.assertEqual(result, expected)

    def test_turns_into_list_if_datapackage_keys_are_objects(self):
        dp = {
            'resources': {"schema": {"fields": [{"name": "test","type": "decimal"}]}},
            'licenses': { "id": "test", "title": "test-license", "url": "test.com"},
            'sources': {'name': 'test', 'web': 'test.com'}
        }
        datapackage = self.to_modify.transform_package(dp)
        self.assertEqual(type(datapackage['resources']), list)
        self.assertEqual(type(datapackage['licenses']), list)
