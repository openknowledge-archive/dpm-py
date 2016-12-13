from .do_configure import configure
from .do_delete import delete, purge
from .do_publish import publish
from .do_validate import validate

import os
import datapackage

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

        # do we need to do this or is it done in datapackage library?
        if not os.path.exists(dppath):
            raise DpmException('No Data Package found at %s. Did not find datapackage.json at %s' % (path, dppath))

        dp = datapackage.DataPackage(dppath)
        return dp


    def _load_config(self, path):
        pass


    def validate(self):
        self.datapackage.validate()

        # should we really check this here? Good question i think ...
        for idx, resource in enumerate(self.datapackage.resources):
            if not exists(resource.local_data_path):
                raise DpmException('Resource at index %s with name % and path %s does not exist on disk' % (
                    idx, resource.name, resource.local_data_path)
                    )

        return True

