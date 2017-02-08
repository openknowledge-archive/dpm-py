# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import click


def echo(message, nl=True, **kwargs):
    """
    Echo with colorful ERROR and OK messages.
    [ERROR] and [OK] will be stripped of brackets and painted red/green.
    """
    for x in re.split('(\[ERROR\]|\[OK\])', message):
        if x == '[ERROR]':
            click.secho('ERROR', **dict(kwargs, fg='red', nl=False))
        elif x == '[OK]':
            click.secho('OK', **dict(kwargs, fg='green', nl=False))
        else:
            click.secho(x, **dict(kwargs, nl=False))
    click.echo('', nl=nl)  # new line

