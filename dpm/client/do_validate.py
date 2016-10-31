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
    Validate datapackage in the current dir. Print validation errors if found and
    then exit. Return datapackage if valid.

    :return:
        DataPackage -- valid DataPackage instance

    """
    if not exists('datapackage.json'):
        secho('FAIL', fg='red', nl=False)
        echo(': Current directory is not a datapackage: datapackage.json not found.')
        sys.exit(1)

    try:
        dp = datapackage.DataPackage('datapackage.json')
    except:
        secho('FAIL', fg='red', nl=False)
        echo(': datapackage.json is malformed')
        sys.exit(1)

    try:
        dp.validate()
    except datapackage.exceptions.ValidationError:
        secho('FAIL', fg='red', nl=False)
        echo(': datapackage.json is invalid.')
        errors = list(dp.iter_errors())
        for n, error in enumerate(errors, 1):
            # TODO: printing error looks very noisy on output, maybe try make it look nice.
            # Printing first line is better, but still cryptic sometimes:
            # https://github.com/frictionlessdata/dpmpy/issues/15#issuecomment-257318423
            if len(errors) > 1:
                echo('    Error %d ' % n, nl=False)
            else:
                echo('    Error: ', nl=False)
            echo(str(error).split('\n')[0])
        sys.exit(1)

    return dp
