# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import hashlib
import base64


def md5_file_chunk(file_name, chunk_size=4096):
    """
    Sometimes the files can be large to fit in memory. So it would
    be good to chunk the file and update the hash.
    This function will read 4096 bytes sequentially and
    feed them to the Md5 function

    :param chunk_size: The chunk size to the file read
    :param file_name: The path of the file
    :return: base64-encoded MD5 hash of the file
    """
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return base64.b64encode(hash_md5.digest()).decode()
