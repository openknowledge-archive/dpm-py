# -*- coding: utf-8 -*-
"""
This code was taken from https://github.com/pypa/pip/tree/master/pip/compat
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import os.path
import sys


def expanduser(path):
    """
    Expand ~ and ~user constructions.

    Includes a workaround for http://bugs.python.org/issue14768
    """
    expanded = os.path.expanduser(path)
    if path.startswith('~/') and expanded.startswith('//'):
        expanded = expanded[1:]
    return expanded


# windows detection, covers cpython and ironpython
WINDOWS = (sys.platform.startswith("win") or
           (sys.platform == 'cli' and os.name == 'nt'))
 
