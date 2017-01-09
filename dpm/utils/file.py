# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import open
from os.path import getsize


class ChunkReader(object):
    """
    Chunked file reader. Implements file read api with ability to
    report read progress to specified callback.

    Usage:
        filestream = ChunkReader('/path/file.csv')
        with click.progressbar(length=filestream.len, label=' ') as bar:
            filestream.on_progress = bar.update
            response = requests.put(url, data=filestream)

    TODO: this approach does not work with sending `files` in mutipart requests.
    """
    on_progress = None

    def __init__(self, path):
        self.len = getsize(path)
        self._file = open(path, 'rb')

    def read(self, size):
        if self.on_progress:
            self.on_progress(128 * 1024)
        return self._file.read(128 * 1024)

