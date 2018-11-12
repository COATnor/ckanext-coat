import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import git
from six.moves import urllib

import os


STORAGE_GIT = '/var/lib/ckan/git'

def _is_resource(obj):
    return 'package_id' in obj


class CoatPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'coat')

    # IPackageController / IResourceController

    def _create_repository(self, context, package, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        repo = git.Repo.init(directory)

    def _add_file(self, context, resource, directory, delete=False):
        if resource['url_type'] != 'upload':
            return
        repo = git.Repo(directory)
        name = resource['name']
        filename = os.path.join(directory, name)
        if os.path.isfile(filename):
            extra = '-' + resource['id']
            name += extra
            filename += extra
        if delete:
            os.remove(filename)
            repo.index.remove([name])
            message = "Remove: " + name
        else:
            urllib.request.urlretrieve(resource['url'], filename)
            repo.index.add([name])
            message = "Add: " + name
        display_name = context['auth_user_obj'].display_name
        email = context['auth_user_obj'].email
        author = git.Actor(display_name, email)
        repo.index.commit(message, author=author)

    def _get_directory(self, context, obj):
        if _is_resource(obj):
            package_show = toolkit.get_action('package_show')
            package = package_show(context, {'id': obj['package_id']})
        else:
            package = obj
        return os.path.join(STORAGE_GIT, package['name'])

    def after_create(self, context, obj):
        directory = self._get_directory(context, obj)
        if _is_resource(obj):
            self._add_file(context, obj, directory)
        else:
            self._create_repository(context, obj, directory)

    def before_delete(self, context, uid, objs):
        for obj in objs:
            directory = self._get_directory(context, obj)
            if _is_resource(obj):
                self._add_file(context, obj, directory, delete=True)
            else:
                pass # empty repo?
