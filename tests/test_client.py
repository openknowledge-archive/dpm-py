import unittest
import os

import datapackage
import pytest
import requests
import responses

from datapackage.exceptions import ValidationError
from mock import patch

from dpm.client import Client, DpmException, ConfigError, JSONDecodeError, HTTPStatusError, ResourceDoesNotExist
from .base import BaseTestCase

dp1_path = 'tests/fixtures/dp1'


class BaseClientTestCase(BaseTestCase):
    # Valid config for tests.
    config = {
        'username': 'user',
        'password': 'password',
        'server': 'http://127.0.0.1:5000'
    }


class ClientInitTest(BaseTestCase):
    """
    `Client.__init__()` should raise exceptions if config is malformed or
    datapackage is missing.
    """
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


class ClientEnsureConfigTest(BaseTestCase):
    def test__ensure_config_password_missing(self):
        """
        When the 'password' is missing in the config, the client should raise ConfigError.
        """
        config = {'username': 'user', 'server': 'server'}
        client = Client(dp1_path, config)

        with pytest.raises(ConfigError):
            client._ensure_config()

        try:
            client._ensure_config()
        except ConfigError as e:
            assert "'password' is required" in str(e)

    def test__ensure_config_username_missing(self):
        """
        When the 'username' is missing in the config, the client should raise ConfigError.
        """
        config = {'password': 'pwd', 'server': 'server'}
        client = Client(dp1_path, config)

        with pytest.raises(ConfigError):
            client._ensure_config()

        try:
            client._ensure_config()
        except ConfigError as e:
            assert "'username' is required" in str(e)

    def test__ensure_config_server_missing(self):
        """
        When the 'server' is missing in the config, the client should raise ConfigError.
        """
        config = {'username': 'user', 'password': 'pwd'}
        client = Client(dp1_path, config)

        with pytest.raises(ConfigError):
            client._ensure_config()

        try:
            client._ensure_config()
        except ConfigError as e:
            assert "'server' is required" in str(e)


class ClientApirequestTest(BaseClientTestCase):
    def setUp(self):
        # GIVEN client instance with valid auth token
        self.client = Client(dp1_path, self.config)
        self.client.token = '123'

    def test_connerror_oserror(self):
        # GIVEN socket that throws OSError
        with patch("socket.socket.connect", side_effect=OSError) as mocksock:
            # WHEN client._apirequest is invoked
            try:
                result = self.client._apirequest(method='POST', url='http://127.0.0.1:5000')
            except Exception as e:
                result = e

            # THEN ConnectionError should be raised
            assert isinstance(result, requests.ConnectionError)

    def test_json_decode_error(self):
        # GIVEN the server that responds with some invalid JSON
        responses.add(
            responses.POST, 'http://127.0.0.1:5000',
            body="some invalid json",
            status=200)

        # WHEN client._apirequest is invoked
        try:
            result = self.client._apirequest(method='POST', url='http://127.0.0.1:5000')
        except Exception as e:
            result = e

        # THEN JSONDecodeError should be raised
        assert isinstance(result, JSONDecodeError)

    def test_http_status_error(self):
        # GIVEN the server that responds with unsuccessful status_code (400)
        responses.add(
            responses.POST, 'http://127.0.0.1:5000',
            json={'message': 'some error'},
            status=400)

        # WHEN client._apirequest is invoked
        try:
            result = self.client._apirequest(method='POST', url='http://127.0.0.1:5000')
        except Exception as e:
            result = e

        # THEN HTTPStatusError should be raised
        assert isinstance(result, HTTPStatusError)

    def test_success(self):
        # GIVEN the server that responds with successful and valid response
        responses.add(
            responses.POST, 'http://127.0.0.1:5000',
            json={'message': 'ok'},
            status=200)

        # WHEN client._apirequest is invoked
        result = self.client._apirequest(method='POST', url='http://127.0.0.1:5000')

        # THEN result should be Response instance
        assert isinstance(result, requests.Response)


class ClientValidateTest(BaseClientTestCase):
    def test_validate_invalid_datapackage_schema(self):
        # GIVEN invalid datapackage (missing resource path)
        invalid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                {"name": "res"}
            ]
        })
        # AND client
        client = Client(dp1_path)
        client.datapackage = invalid_dp

        # WHEN validate() is invoked
        try:
            result = client.validate()
        except Exception as e:
            result = e

        # THEN ValidationError should be raised
        assert isinstance(result, ValidationError)
        # AND it should say some cryptic message on invalid schema
        assert "not valid under any of the given schemas" in str(result)

    def test_validate_missing_datapackage_resource_file(self):
        # GIVEN datapackage without resource file on disk
        invalid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                {"name": "res-asd", "path": "./data/some_data.csv"}
            ]
        })
        # AND client
        client = Client(dp1_path)
        client.datapackage = invalid_dp

        # WHEN validate() is invoked
        try:
            result = client.validate()
        except Exception as e:
            result = e

        # THEN ResourceDoesNotExist should be raised
        assert isinstance(result, ResourceDoesNotExist)
        # AND it should say that resource does not exist
        assert "data/some_data.csv does not exist on disk" in str(result)

