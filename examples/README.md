The script `import_git.py` is an example how we can programmatically
publish data to data package registry.
In this example shows how we can import data package from github.

We have two option here.

- Import from single data package repository in github
- Import from list of data package repositories in github

Example:
We need to install `gitpython` to use this example

```
$ pip install gitpython
```

Import from single data package repository in github

```
$ python import_git.py https://github.com/datasets/s-and-p-500-companies
```

Import from list of data package repositories in github

```
$ python import_git.py https://raw.githubusercontent.com/datasets/registry/master/core-list.txt -t multiple
```