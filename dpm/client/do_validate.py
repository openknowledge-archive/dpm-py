# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
import sys
from os.path import exists


def validate():
    """
    Validate datapackage in the current dir. Print validation errors if found and
    then exit. Return datapackage if valid.

    :return:
        DataPackage -- valid DataPackage instance

    """
    if not exists('datapackage.json'):
        print('Current directory is not a datapackage: datapackage.json not found.')
        sys.exit(1)

    try:
        dp = datapackage.DataPackage('datapackage.json')
    except:
        print('datapackage.json is malformed')
        sys.exit(1)

    try:
        dp.validate()
    except datapackage.exceptions.ValidationError:
        for error in dp.iter_errors():
            # TODO: printing error looks very noisy on output, maybe try make it look nice.
            print(error)
        sys.exit(1)

    return dp
