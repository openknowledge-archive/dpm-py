Dpm is a datapackage manager. For more about data packages see http://frictionlessdata.io/data-packages/

## Install

Until the new code available on pypi, you can install it from this repo:

```
[sudo] pip install git+https://github.com/frictionlessdata/dpmpy.git
```

## Configuration

Dpm can be configured using `dpmpy configure` command. It will ask you
to provide username, password and server address of datapackage registry.

The config is stored in ~/.dpm/config, you can edit it with text editor.
Simple example config file can look like this:

```
username = myname
password = mypass
server = https://example.com
```

## Testing

1. Clone the repo 

2. Run `python setup.py test`

