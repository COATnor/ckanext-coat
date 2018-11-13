import ckanext.coat.helpers as helpers
import ckan.plugins.toolkit as toolkit

import git

import os
from six.moves import urllib

STORAGE_GIT = '/var/lib/ckan/git'

def get_directory(context, obj):
    if helpers.is_resource(obj):
        package_show = toolkit.get_action('package_show')
        package = package_show(context, {'id': obj['package_id']})
    else:
        package = obj
    return os.path.join(STORAGE_GIT, package['name'])

def create_repository(package, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    git.Repo.init(directory)

def set_author(context, obj, directory):
    display_name = context['auth_user_obj'].display_name
    email = context['auth_user_obj'].email
    repo = git.Repo(directory)
    with repo.config_writer() as config:
        config.set_value("user", "name", display_name)
        config.set_value("user", "email", email)

def add_file(resource, directory, delete=False):
    if resource['url_type'] != 'upload':
        return
    repo = git.Repo(directory)
    name = resource['name']
    filename = os.path.join(directory, name)
    if delete:
        os.remove(filename)
        repo.index.remove([name])
        message = "Remove: " + name
    else:
        if os.path.isfile(filename):
            extra = '-' + resource['id']
            name += extra
            filename += extra
        urllib.request.urlretrieve(resource['url'], filename)
        repo.index.add([name])
        message = "Add: " + name
    repo.index.commit(message)

def new_release(package, directory):
    version = "v" + package['version']
    message = "New release: " + version
    repo = git.Repo(directory)
    repo.create_tag(version, message=message)
