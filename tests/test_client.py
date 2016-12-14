import unittest
import pytest
import os

from dpm.client import Client, DpmException, ConfigError

dp1_path = 'tests/fixtures/dp1'

class TestClient(unittest.TestCase):
    config = {
        'username': 'user',
        'password': 'password',
        'server': 'http://127.0.0.1:5000'
    }

    def test___init__fails_no_data_package(self):
        with pytest.raises(DpmException):
            client = Client(self.config)
        try:
            client = Client(self.config)
        except DpmException as e:
            assert e.message.startswith('No Data Package found at %s' %
                    os.getcwd())
    
    def test___init__datapackage_ok(self):
        client = Client(self.config, dp1_path)
        assert client.datapackage
        assert client.datapackage.base_path.endswith(dp1_path)

    def test__init__config_password_missing(self):
        """
        When the 'password' is missing in the config, the client should raise ConfigError.
        """
        config = {'username': 'user', 'server': 'server'}
        with pytest.raises(ConfigError):
            client = Client(config, dp1_path)

        try:
            client = Client(config, dp1_path)
        except ConfigError as e:
            assert "'password' is required" in e.message

    def test__init__config_username_missing(self):
        """
        When the 'username' is missing in the config, the client should raise ConfigError.
        """
        config = {'password': 'pwd', 'server': 'server'}
        with pytest.raises(ConfigError):
            client = Client(config, dp1_path)

        try:
            client = Client(config, dp1_path)
        except ConfigError as e:
            assert "'username' is required" in e.message

    def test__init__config_server_missing(self):
        """
        When the 'server' is missing in the config, the client should raise ConfigError.
        """
        config = {'username': 'user', 'password': 'pwd'}

        with pytest.raises(ConfigError):
            client = Client(config, dp1_path)

        try:
            client = Client(config, dp1_path)
        except ConfigError as e:
            assert "'server' is required" in e.message


    # TODO: test validate

