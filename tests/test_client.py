import unittest
import pytest
import os

from dpm.client import Client, DpmException

dp1_path = 'tests/fixtures/dp1'

class TestClient(unittest.TestCase):
    def test___init__fails_no_data_package(self):
        with pytest.raises(DpmException):
            client = Client()
        try:
            client = Client()
        except DpmException as e:
            assert e.message.startswith('No Data Package found at %s' %
                    os.getcwd())
    
    def test___init__datapackage_ok(self):
        client = Client(dp1_path)
        assert client.datapackage
        assert client.datapackage.base_path.endswith(dp1_path)

    def test__init__config_ok(self):
        pass
    
    # TODO: test validate

