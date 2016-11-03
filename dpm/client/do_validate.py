# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
from os.path import exists

import datapackage
from click import echo, secho


def validate():
    """
    Validate datapackage in the current directory. If package is invalid - print
    validation errors and exit. Return datapackage if valid.

    :return:
        DataPackage -- valid DataPackage instance

    """
    if not exists('datapackage.json'):
        secho('FAIL', fg='red', nl=False)
        echo(' Current directory is not a datapackage: datapackage.json not found.\n')
        sys.exit(1)

    try:
        dp = datapackage.DataPackage('datapackage.json')
    except:
        # TODO: show more dtailed error message - at least line number
        # See also: https://github.com/frictionlessdata/datapackage-py/issues/113
        secho('FAIL', fg='red', nl=False)
        echo(' datapackage.json is malformed\n')
        sys.exit(1)

    try:
        dp.validate()
    except datapackage.exceptions.ValidationError:
        secho('FAIL', fg='red', nl=False)
        echo(' datapackage.json is invalid.\n')
        errors = list(dp.iter_errors())
        for n, error in enumerate(errors, 1):
            if len(errors) > 1:
                echo('Error %d ' % n, nl=False)
            else:
                echo('Error: ', nl=False)
            # TODO: printing error looks very noisy on output, maybe try to make it look nice.
            # Printing first line is better, but still cryptic sometimes:
            # https://github.com/frictionlessdata/dpmpy/issues/15#issuecomment-257318423
            echo('%s\n' % str(error).split('\n')[0])
        sys.exit(1)

    nonexisting = [x for x in dp.resources if not exists(x.local_data_path)]
    if nonexisting:
        secho('FAIL', fg='red', nl=False)
        echo(' resource does not exist:')
        for resource in nonexisting:
            echo(' %s' % resource.local_data_path)
        echo('')
        sys.exit(1)

    return dp
