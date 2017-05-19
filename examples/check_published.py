"""
This script cheks if all the packages published by publisher on Datahub are working
fine and returning status 200.

By default script awaits that dpm credentials are set in ~/.dpm/config and getting
Publisher and Server to check against from there. You can also set this argguments
by adding optional -p (--publisher) publisher_name and -s (--server) server_url
flags when running script
"""
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from dpm import client, config
import subprocess
import argparse
import requests

def parse_arguments():
    '''
    Parse CLI
    '''
    arg = argparse.ArgumentParser()
    arg.add_argument("-p", "--publisher",
                     help="Publisher name")
    arg.add_argument("-s", "--server",
                     help="Server domain that DataPackages should be published. Eg: https://www.datapackaged.com")
    return arg.parse_args()


def get_published_datapackages(publisher, server):
    '''
    Returns list of urls for published datapackages
    '''
    if parse_arguments().publisher:
        publisher=parse_arguments().publisher
    if parse_arguments().server:
        server=parse_arguments().server
    if not publisher:
        raise Exception('Publisher name is required - please run same command with  -p publisher-name. Run with -h for help')
    if not server:
        raise Exception('Server name is required - please run same command with  -p server-name. Run with -h for help')
    if server.endswith('/'):
        server = server[:-1]
    url = '%s/api/package/%s'%(server, publisher)
    res = requests.get(url)
    datapackages = ['%s/%s/%s'%(server, publisher, package)  for package in res.json().get('data')]
    return datapackages

def check_200(links):
    '''
    checks if status code for link is 200. returns list ones that is not 200
    '''
    not_ok = []
    for link in links:
        status = requests.get(link).status_code
        if status != 200:
            not_ok.append({'package': link, 'status': status})
    return not_ok

def run():
    try:
        conf = config.read_config()
        published_packages = get_published_datapackages(publisher=conf.get('username'), server=conf.get('server'))
        print ('\nChecking if published datapackages are OK ...')
        problems = check_200(published_packages)
        print ('\n---------------------------------------------\n')
        if len (problems):
            print ('\nFollowing packages have problems after being published:\n')
        else:
            print ('Everything is OK')
        for package in problems:
            print ('%s | status code: %s'%(package['package'], package['status']))

    except Exception as e:
        print(e)

if __name__ == '__main__':
    run()
