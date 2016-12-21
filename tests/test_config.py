# -*- coding: utf-8 -*-
import unittest
import os

import pytest

import dpm.config

class TestConfig(unittest.TestCase):

    def test_config_from_file(self):
        config_path = 'tests/fixtures/config.ini'   
        config = dpm.config.read_config(config_path)
        assert config['username'] == 'abc-test'

    def test_config_from_file_fails_if_config_path_does_not_exist(self):
        config_path = 'bad/path/to/config.ini'   
        with pytest.raises(Exception):
            config = dpm.config.read_config(config_path)
        try:
            config = dpm.config.read_config(config_path)
        except Exception as e:
            assert str(e).startswith('No config file found')
    
    def test_config_from_env(self):
        os.environ['DPM_USERNAME'] = 'xyz'
        config = dpm.config.read_config()
        assert config['username'] == 'xyz'
        del os.environ['DPM_USERNAME']

