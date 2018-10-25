import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.coat.logic.action.create
import ckanext.coat.logic.action.get
import ckanext.coat.logic.action.update


class CoatPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'coat')

    # IActions

    def get_actions(self):
        return {
            'ckan_package_create':
            ckanext.coat.logic.action.create.ckan_package_create,
            'package_create':
            ckanext.coat.logic.action.create.package_create,
            'ckan_package_search':
            ckanext.coat.logic.action.get.ckan_package_search,
            'package_search':
            ckanext.coat.logic.action.get.package_search,
            'ckan_package_update':
            ckanext.coat.logic.action.update.ckan_package_update,
            'package_update':
            ckanext.coat.logic.action.update.package_update,
        }
