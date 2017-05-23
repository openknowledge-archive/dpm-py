'''
This script is used to fix commmon issues for datapackage.json, like changing yet
unsupported date formats for fields with type date, or unsupported types for
numeric fields.
Script also fixes commonly made mistake while creating datapackage.json. According
to Frictionless Data spec metadata describing data should not directly be objects,
but elements of the list Eg:

## Bad
{
  "name": "example",
  "licenses": {
    "name": "example license",
    "url": "https://example/license.com"
  }
}

## Good
{
  "name": "example",
  "licenses": [
    {
    "name": "example license",
    "url": "https://example/license.com"
    }
  ]
}

Script can be used form Command Line Interface (CLI).
`python modify.py --help` for instructions
'''

import json

class Modify(object):
    def __init__(self, path='datapackage.json'):
        self.path = path

    def transform_package(self, data):
        '''Transform data
        '''
        unsupported_number_types = [
            'decimal', 'double', 'float', 'binary'
        ]
        for item in data:
            if type(data[item]) is dict:
                data[item] = [data[item]]
        for res_idx in range (len(data['resources'])):
            fields = data['resources'][res_idx]['schema']['fields']
            for field_idx in range(len(fields)):
                field = data['resources'][res_idx]['schema']['fields'][field_idx]
                if field['type'] == 'date':
                    data['resources'][res_idx]['schema']['fields'][field_idx]['format'] = "any"
                if field['type'] in unsupported_number_types:
                    data['resources'][res_idx]['schema']['fields'][field_idx]['type'] = "number"
        return data

    def modify(self):
        '''Rewrites datapackage.json
        '''
        transformed_data = self.transform_package(json.load(open(self.path)))
        jsonfile = open(self.path , 'w')
        json.dump(transformed_data, jsonfile,  indent=2)

    def show(self):
        '''See modified datapackage.json as a json string
        '''
        transformed_data = self.transform_package(json.load(open(self.path)))
        print (json.dumps(transformed_data, indent=2))

## ==============================================
## CLI

import sys
import optparse
import inspect

def _object_methods(obj):
    methods = inspect.getmembers(obj, inspect.ismethod)
    methods = filter(lambda (name, y): not name.startswith('_'), methods)
    methods = dict(methods)
    return methods

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}
Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

if __name__ == '__main__':
    _main(Modify)
