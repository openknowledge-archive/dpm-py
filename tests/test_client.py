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
    
