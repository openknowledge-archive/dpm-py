from .do_configure import configure
from .do_delete import delete, purge
from .do_publish import publish
from .do_validate import validate

import os

class DpmException(Exception):
    pass

class Client(object):

    def __init__(self, data_package_path='', config_path="~/.dpm/config", click=None):
        if not data_package_path:
            data_package_path = os.getcwd()
        data_package_path = os.path.abspath(data_package_path)
        # may want to use the datapackage-py here
        self.datapackage = self._load_dp(data_package_path)

        # load config ... 
        self.config = self._load_config(config_path)

        self.click = click

    def _load_dp(self, path):
        dppath = os.path.join(path, 'datapackage.json')
        if not os.path.exists(dppath):
            raise DpmException('No Data Package found at %s. Did not find datapackage.json at %s' % (path, dppath))
        dp = datapackage.DataPackage('datapackage.json')

    def _load_config(self, path):
        pass

