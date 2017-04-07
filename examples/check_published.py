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
    arg.add_argument("link", help="link or the path to file containing list of names or Git urls for DataPackages")
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
    datapackages = ['%s/%s/%s'%(server, publisher, package[0])  for package in res.json().get('data')]
    return datapackages


def get_datapackages(url):
    '''
    Returns list of git urls
    '''
    if url.startswith("http://") or url.startswith("https://"):
        response = requests.get(url).text
    elif url.startswith("file://"):
        response = open(url, 'r').read()
    else:
        raise Exception('No valid protocol url should start with http://, https:// or file://')
    datapackages = []
    for package in response.split('\n'):
        if package:
            datapackages.append(package)
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
        arguments = parse_arguments()
        print ('\nCheking for publishing datapackages')
        errors = subprocess.check_output(['python', 'import_git.py', arguments.link, '-t', 'multiple'])
        total_packages = get_datapackages(arguments.link)
        conf = config.read_config()
        published_packages = get_published_datapackages(publisher=conf.get('username'), server=conf.get('server'))

        print ('\n%s out of %s datapackages are published'%(len(published_packages), len(total_packages)))
            with open('not_published.txt', 'w') as f:
            f.write(errors[errors.find('Warning: Following datasets were skiped'):])
        print ('See reasons in errors.txt')

        print ('\nChecking if published datapackages are OK ...')
        problems = check_200(published_packages)
        print ('\n---------------------------')
        print ('\nFollowing packages have problems after being published:\n')
        for package in problems:
            print ('%s | status code: %s'%(package['package'], package['status']))

    except Exception as e:
        print(e)

if __name__ == '__main__':
    run()
