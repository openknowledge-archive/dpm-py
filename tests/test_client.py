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
from mock import patch, mock_open

from dpm.client import Client, DpmException, ConfigError, JSONDecodeError, HTTPStatusError, ResourceDoesNotExist
from .base import BaseTestCase
from .base import jsonify

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
            assert str(e).startswith('No Data Package found at %s' %
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
                'password': 'password'
            }
        client = Client(dp1_path, config)
        # GIVEN the registry server that accepts any user
        responses.add(
            responses.POST, 'https://example.com/api/auth/token',
            json={'token': 'blabla'},
            status=200)
        # AND registry server accepts any datapackage
        responses.add(
            responses.PUT, 'https://example.com/api/package/%s/%s' % (username,
                dp_name),
            json={'message': 'OK'},
            status=200)
        # AND registry server gives bitstore upload url
        responses.add(
            responses.POST, 'https://example.com/api/auth/bitstore_upload',
            json={'key': 'https://s3.fake/put_here'},
            status=200)
        # AND s3 server allows data upload
        responses.add(
            responses.PUT, 'https://s3.fake/put_here',
            json={'message': 'OK'},
            status=200)
        # AND registry server successfully finalizes upload
        responses.add(
            responses.POST, 'https://example.com/api/package/%s/%s/finalize' % (username, dp_name),
            json={'message': 'OK'},
            status=200)

        # WHEN `dpm publish` is invoked
        result = client.publish(publisher='testpub')

        # 7 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "password"}),
                # PUT metadata with datapackage.json contents
                ('PUT', 'https://example.com/api/package/%s/%s' % (username, dp_name),
                    client.datapackage.to_dict()),
                # POST authorize presigned url for s3 upload
                ('POST', 'https://example.com/api/auth/bitstore_upload',
                    {"publisher": username, "package": dp_name,
                     "path": "data/some-data.csv", "md5": '365bb8566485f194fac0ae108cbf22cb'}),
                # PUT data to s3
                ('PUT', 'https://s3.fake/put_here', b'A,B,C\n1,2,3\n'),
                # POST authorized presigned url for README
                ('POST', 'https://example.com/api/auth/bitstore_upload',
                    {"publisher": username, "package": dp_name,
                     "path": "README.md", "md5": 'd8e0da4070aaa1d3b607f71b7f4de580'}),
                # PUT README to S3
                ('PUT', 'https://s3.fake/put_here', b'This is a Data Package.\n'),
                # POST finalize upload
                ('POST', 'https://example.com/api/package/%s/%s/finalize' %
                    (username, dp_name), '')])


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
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'http://127.0.0.1:5000/api/auth/token',
                    {"username": "user", "secret": "password"}),
                # DELETE datapackage
                ('DELETE', 'http://127.0.0.1:5000/api/package/user/some-datapackage', '')])

    def test_purge_success(self):
        # WHEN purge() is invoked
        self.client.purge()

        # THEN 2 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body))
             for x in responses.calls],
            [
                # POST authorization
                ('POST', 'http://127.0.0.1:5000/api/auth/token',
                    {"username": "user", "secret": "password"}),
                # DELETE datapackage
                ('DELETE', 'http://127.0.0.1:5000/api/package/user/some-datapackage/purge', '')])
