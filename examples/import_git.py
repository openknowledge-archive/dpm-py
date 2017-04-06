# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import argparse
import os
import shutil
import git
import requests
from dpm import client, config

DIR_NAME_PREFIX = "/tmp/dp_clone"


def parse_arguments():
    arg = argparse.ArgumentParser("python import_from_git.py ")
    arg.add_argument("link", help="Git link or the file containing data package git links")
    arg.add_argument("-t", "--type", choices=['single', 'multiple'], default='single',
                     help="Type of the link. Single for one data package git link. Multiple for "
                          "path of the file contains list of datapackage links, this can be "
                          "file:///some.txt or http://somefile.txt")
    return arg.parse_args()


def publish_data_package(git_url, count=0):
    if git_url.startswith("http://") or git_url.startswith("https://"):
        dir_name = DIR_NAME_PREFIX + "/" + str(count)
        clone_git_repo(git_url=git_url, dir_name=dir_name)
        conf = config.read_config()
        client.Client(data_package_path=dir_name, config=conf).publish()


def clone_git_repo(git_url, dir_name):
    if git_url.startswith("http://") or git_url.startswith("https://"):
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        os.mkdir(dir_name)
        repo = git.Repo.init(dir_name)
        print("cloning : " + git_url)
        origin = repo.create_remote('origin', git_url)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)


def get_all_git_url(url):
    if url.startswith("http://") or url.startswith("https://"):
        response = requests.get(url).text
    elif url.startswith("file://"):
        response = open(url, 'r').read()
    else:
        raise Exception('No valid protocol url should start with http://, https:// or file://')
    count = 0
    datapackage_urls = dict()
    for git_url in response.split('\n'):
        datapackage_urls[count] = git_url
        count += 1
    return datapackage_urls


def run():
    try:
        if not os.path.isdir(DIR_NAME_PREFIX):
            os.mkdir(DIR_NAME_PREFIX)

        arguments = parse_arguments()
        if arguments.type == 'single':
            publish_data_package(arguments.link)
        elif arguments.type == 'multiple':
            urls = get_all_git_url(arguments.link)
            failed = []
            for k, v in urls.items():
                try:
                    publish_data_package(git_url=v, count=k)
                except Exception as e:
                    failed.append({'dataset': v, 'error': e})
            print ('\nWarning: Following datasets were skiped as failed to publish:\n')
            for package in failed:
                print ('---\n\nDataSet: %s\n\nREASON: %s' %(package.get('dataset'), package.get('error')))

        if os.path.isdir(DIR_NAME_PREFIX):
            shutil.rmtree(DIR_NAME_PREFIX)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    run()
