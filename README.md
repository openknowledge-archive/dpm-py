# Data Package Manager - in Python

[![Gitter](https://img.shields.io/gitter/room/frictionlessdata/chat.svg)](https://gitter.im/frictionlessdata/chat)
[![Build Status](https://travis-ci.org/frictionlessdata/dpm-py.svg?branch=master)](https://travis-ci.org/frictionlessdata/dpm-py)
[![Test Coverage](https://coveralls.io/repos/frictionlessdata/dpm-py/badge.svg?branch=master&service=github)](https://coveralls.io/github/frictionlessdata/dpm-py)
![Support Python versions 2.7, 3.3, 3.4 and 3.5](https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5-blue.svg)

dpm[py] is a command-line [data package][dp] manager written in Python. You can use it to publish and install data packages from a data package registry server. For more about data packages see http://frictionlessdata.io/data-packages

[dp]: http://frictionlessdata.io/data-packages

## Install

Until the new code available on pypi, you can install it from this repo:

```
[sudo] pip install git+https://github.com/frictionlessdata/dpm-py.git
```

## Configuration

Dpmpy can be configured using `dpmpy configure` command. It will ask you
to provide username, password and server address of datapackage registry.

The config is stored in ~/.dpm/config, you can edit it with text editor.
Simple example config file can look like this:

```
username = myname
password = mypass
server = https://example.com
```

## Usage

To publish datapackage, go to the datapackage directory (with datapackage.json) and
launch `dpmpy publish`. If your configured username and password are correct, dpmpy will
upload datapackage.json and all relevant resources to the registry server.

## Testing

1. Clone the repo 

2. Run `python setup.py test`

