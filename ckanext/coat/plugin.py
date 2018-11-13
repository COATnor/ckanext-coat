import ckanext.coat.logic.git_archive as git_archive
import ckanext.coat.helpers as helpers
import ckanext.coat.logic.action.update
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class CoatPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'coat')

    # IPackageController / IResourceController

    def after_create(self, context, obj):
        directory = git_archive.get_directory(context, obj)
        if helpers.is_resource(obj):
            git_archive.set_author(context, obj, directory)
            git_archive.add_file(obj, directory)
        else:
            git_archive.create_repository(obj, directory)

    def before_delete(self, context, uid, objs):
        for obj in objs:
            directory = git_archive.get_directory(context, obj)
            git_archive.set_author(context, obj, directory)
            if helpers.is_resource(obj):
                git_archive.add_file(obj, directory, delete=True)
            else:
                pass # empty repo?

    # IActions

    def get_actions(self):
        return {
            'ckan_package_update':
            ckanext.coat.logic.action.update.ckan_package_update,
            'package_update':
            ckanext.coat.logic.action.update.package_update,
        }
