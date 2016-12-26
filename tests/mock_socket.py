# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import socket


class NetworkDisabled(Exception):
    pass


class MockSocket(object):
    def __init__(*args, **kwargs):
        pass

    def connect(*args, **kwargs):
        raise NetworkDisabled("Network is disabled")

    def close(*args, **kwargs):
        pass

    def setsockopt(*args, **kwargs):
        pass

    def settimeout(*args, **kwargs):
        pass


def getaddrinfo(host, port, family=None, socktype=None, proto=None, flags=None):
    return [(2, 1, 6, '', (host, port))]


def create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, sender_address=None):
    s = MockSocket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
        s.settimeout(timeout)
    s.connect(address)
    return s


def patch_socket():
    socket.socket = MockSocket
    socket.socket = socket.__dict__['socket'] = MockSocket
    socket._socketobject = socket.__dict__['_socketobject'] = MockSocket
    socket.SocketType = socket.__dict__['SocketType'] = MockSocket
    socket.create_connection = socket.__dict__['create_connection'] = create_connection
    socket.getaddrinfo = socket.__dict__['getaddrinfo'] = getaddrinfo
    socket.gethostname = socket.__dict__['gethostname'] = lambda: 'localhost'
    socket.gethostbyname = socket.__dict__['gethostbyname'] = lambda host: '127.0.0.1'
    socket.inet_aton = socket.__dict__['inet_aton'] = lambda host: '127.0.0.1'

