import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.coat.logic.action.create


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
        }
