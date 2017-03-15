# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import unittest
import os

import datapackage
import pytest
import requests
import responses

from datapackage.exceptions import ValidationError
from mock import patch, mock_open, MagicMock, Mock

from dpm.client import Client, DpmException, ConfigError, JSONDecodeError, HTTPStatusError, ResourceDoesNotExist, AuthResponseError
from .base import BaseTestCase
from .base import jsonify

dp1_path = 'tests/fixtures/dp1'
dp2_path = 'tests/fixtures/dp2'


class BaseClientTestCase(BaseTestCase):
    # Valid config for tests.
    config = {
        'username': 'user',
        'access_token': 'access_token',
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
            assert str(e).startswith('No Data Package found at %s' %
                    os.getcwd())
    
    def test___init__datapackage_ok(self):
        client = Client(dp1_path)
        assert client.datapackage
        assert client.datapackage.base_path.endswith(dp1_path)


class ClientEnsureConfigTest(BaseTestCase):
    def test__ensure_config_access_token_missing(self):
        """
        When the 'access_token' is missing in the config, the client should raise ConfigError.
        """
        config = {'username': 'user', 'server': 'server'}
        client = Client(dp1_path, config)

        with pytest.raises(ConfigError):
            client._ensure_config()

        try:
            client._ensure_config()
        except ConfigError as e:
            assert "'access_token' is required" in str(e)

    def test__ensure_config_username_missing(self):
        """
        When the 'username' is missing in the config, the client should raise ConfigError.
        """
        config = {'access_token': 'pwd', 'server': 'server'}
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
        config = {'username': 'user', 'access_token': 'pwd'}
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
            },
            default_base_path='.')
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

    def test_skip_validate_non_tabular_data_package(self):
        client = Client(dp2_path, datavalidate=True)
        result = client.validate()
        self.assertTrue(result)


class ClientPublishSuccessTest(BaseClientTestCase):
    """
    When user publishes valid datapackage, and server accepts it, dpm should
    report sucess.
    """

    def test_publish_success(self):
        # name from fixture data package
        dp_name = 'abc'
        username = 'user'
        config = {
                'username': username,
                'server': 'https://example.com',
                'access_token': 'access_token'
            }
        client = Client(dp1_path, config)
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)

        # AND registry server gives bitstore upload url
        responses.add(
            responses.POST, 'https://example.com/api/datastore/authorize',
            json={
                'filedata': {
                    'datapackage.json': {'upload_url': 'https://s3.fake/put_here_datapackege',
                                         'upload_query': {'key': 'k'}},
                    'README.md': {'upload_url': 'https://s3.fake/put_here_readme',
                                  'upload_query': {'key': 'k'}},
                    'data/some-data.csv': {'upload_url': 'https://s3.fake/put_here_resource',
                                           'upload_query': {'key': 'k'}}
                }
            },
            status=200)
        # AND s3 server allows data upload for datapackage
        responses.add(
            responses.POST, 'https://s3.fake/put_here_datapackege',
            json={'message': 'OK'},
            status=200)
        # AND s3 server allows data upload for readme
        responses.add(
            responses.POST, 'https://s3.fake/put_here_readme',
            json={'message': 'OK'},
            status=200)
        # AND s3 server allows data upload for resource
        responses.add(
            responses.POST, 'https://s3.fake/put_here_resource',
            json={'message': 'OK'},
            status=200)
        # AND registry server successfully finalizes upload
        responses.add(
            responses.POST, 'https://example.com/api/package/upload',
            json={'status': 'queued'},
            status=200)

        # WHEN publish() is invoked
        result = client.publish(publisher='testpub')

        # 6 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # POST authorize presigned url for s3 upload
                ('POST', 'https://example.com/api/datastore/authorize',
                 {
                     'metadata': {
                         'owner': 'user',
                         'name': 'abc'
                     },
                     'filedata': {
                         "README.md": {
                             "md5": '2ODaQHCqodO2B/cbf03lgA==',
                             "size": 24,
                             "type": 'binary/octet-stream',
                             'name': 'README.md'
                         },
                         "datapackage.json": {
                             "md5": 'mDmEykSS++mJF3SaWW56kw==',
                             "size": 120,
                             "type": 'application/json',
                             'name': 'datapackage.json'
                         },
                         "data/some-data.csv": {
                             "md5": 'Nlu4VmSF8ZT6wK4QjL8iyw==',
                             "size": 12,
                             "type": 'binary/octet-stream',
                             'name': 'data/some-data.csv'
                         }
                     }
                 }),
                # POST data to s3
                ('POST', 'https://s3.fake/put_here_datapackege', ''),
                ('POST', 'https://s3.fake/put_here_readme', ''),
                ('POST', 'https://s3.fake/put_here_resource', ''),
                # POST finalize upload
                ('POST', 'https://example.com/api/package/upload',
                 {'datapackage': 'https://s3.fake/put_here_datapackege/k'})
            ])


class PublishInvalidTest(BaseClientTestCase):
    """
    When user publishes datapackage, which is deemed invalid by server, the error message should
    be displayed.
    """
    @unittest.skip("INVALID NO VALIDATION CHECK FOR datapackage.json")
    def test_publish_invalid(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
                "name": "some-datapackage",
                "resources": [
                    { "name": "some-resource", "path": "./data/some_data.csv", }
                ]
            },
            default_base_path='.')
        patch('dpm.client.DataPackage', lambda *a: self.valid_dp).start()
        patch('dpm.client.exists', lambda *a: True).start()

        # AND the server that accepts any user
        responses.add(
                responses.POST, 'http://127.0.0.1:5000/api/auth/token',
                json={'token': 'blabla'},
                status=200)
        # AND server rejects any datapackage as invalid
        responses.add(
                responses.PUT, 'http://127.0.0.1:5000/api/package/user/some-datapackage',
                json={'message': 'invalid datapackage json'},
                status=400)

        # AND the client
        client = Client(dp1_path, self.config)

        # WHEN publish() is invoked
        try:
            result = client.publish()
        except Exception as e:
            result = e

        # THEN HTTPStatusError should be raised
        assert isinstance(result, HTTPStatusError)
        # AND 'invalid datapackage json' should be printed to stdout
        self.assertRegexpMatches(str(result), 'invalid datapackage json')


class ClientDeletePurgeSuccessTest(BaseClientTestCase):
    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                {"path": "./data/some_data.csv", }
            ]
        })
        # AND client
        self.client = Client(dp1_path, self.config)
        self.client.datapackage = valid_dp

        # AND the registry server that accepts any user
        responses.add(
            responses.POST, 'http://127.0.0.1:5000/api/auth/token',
            json={'token': 'blabla'},
            status=200)
        # AND registry server accepts deletion of any datapackage
        responses.add(
            responses.DELETE, 'http://127.0.0.1:5000/api/package/user/some-datapackage',
            json={'message': 'OK'},
            status=200)
        # AND registry server accepts purging of any datapackage
        responses.add(
            responses.DELETE, 'http://127.0.0.1:5000/api/package/user/some-datapackage/purge',
            json={'message': 'OK'},
            status=200)

    def test_delete_success(self):
        # WHEN delete() is invoked
        self.client.delete()

        # THEN 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'http://127.0.0.1:5000/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # DELETE datapackage
                ('DELETE', 'http://127.0.0.1:5000/api/package/user/some-datapackage', '')])

    def test_purge_success(self):
        # WHEN purge() is invoked
        self.client.purge()

        # THEN 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'http://127.0.0.1:5000/api/auth/token',
                    {"username": "user", "secret": "access_token"}),
                # DELETE datapackage
                ('DELETE', 'http://127.0.0.1:5000/api/package/user/some-datapackage/purge', '')])

                
class ClientEnsureAuthEmptyTokenTest(BaseClientTestCase):
    """
    When registry(auth) server returns empty auth token client should raise error.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
                "name": "some-datapackage",
                "resources": [
                    {"name": "some-resource", "path": "./data/some_data.csv", }
                ]
            },
            default_base_path='.')
        patch('dpm.client.DataPackage', lambda *a: self.valid_dp).start()
        patch('dpm.client.exists', lambda *a: True).start()

    def test_getting_empty_auth_token(self):
        # GIVEN registry server that returns empty token
        responses.add(
                responses.POST, 'http://127.0.0.1:5000/api/auth/token',
                json={"token": ""},
                status=200)

        # AND the client
        client = Client(dp1_path, self.config)

        # WHEN _ensure_auth() is called
        try:
            result = client._ensure_auth()
        except Exception as e:
            result = e

        # THEN AuthResponseError should be raised
        assert isinstance(result, AuthResponseError)
        # AND 'server did not return auth token' should be printed to stdout
        self.assertRegexpMatches(str(result), 'Server did not return auth token')


class ClientEnsureAuthSuccessTest(BaseClientTestCase):
    """
    When registry(auth) server returns valid auth token, client should store it.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
                "name": "some-datapackage",
                "resources": [
                    {"name": "some-resource", "path": "./data/some_data.csv", }
                ]
            },
            default_base_path='.')
        patch('dpm.client.DataPackage', lambda *a: self.valid_dp).start()
        patch('dpm.client.exists', lambda *a: True).start()

    def test_ensure_auth_success(self):
        # GIVEN (auth)registry server that returns valid token
        responses.add(
                responses.POST, 'http://127.0.0.1:5000/api/auth/token',
                json={"token": "12345"},
                status=200)

        # AND the client
        client = Client(dp1_path, self.config)

        # WHEN _ensure_auth() is called
        try:
            result = client._ensure_auth()
        except Exception as e:
            result = e

        # THEN token should be returned in result
        assert result == '12345'
        # AND client should store the token
        assert client.token == '12345'

