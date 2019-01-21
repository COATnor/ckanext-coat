import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.coat.logic.action.create
import ckanext.coat.logic.action.get
import ckanext.coat.logic.action.update
import ckanext.coat.logic.action.delete
import ckanext.coat.auth as auth
from ckanext.coat import helpers
import routes.mapper

import requests

CKAN_SCHEMA = 'http://solr:8983/solr/ckan/schema'

class CoatPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IAuthFunctions

    def get_auth_functions(self):
        return {'embargo_access': auth.embargo_access}

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'coat')
        self._custom_schema()

    def _custom_schema(self):
        response = requests.get(CKAN_SCHEMA+'/copyfields')
        copyfields = response.json()['copyFields']
        if {"dest": "version_i", "source": "version"} in copyfields:
           return
        requests.post(CKAN_SCHEMA, json={
            "add-field":{
                "name": "version_i",
                "type": "int",
                "stored": True,
            }
        })
        requests.post(CKAN_SCHEMA, json={
            "add-copy-field":{
                "source": "version",
                "dest": ["version_i"],
            }
        })

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
            'package_show':
            ckanext.coat.logic.action.get.package_show,
            'package_update':
            ckanext.coat.logic.action.update.package_update,
            'ckan_package_delete':
            ckanext.coat.logic.action.delete.ckan_package_delete,
            'package_delete':
            ckanext.coat.logic.action.delete.package_delete,
            'ckan_resource_show':
            ckanext.coat.logic.action.get.ckan_resource_show,
            'resource_show':
            ckanext.coat.logic.action.get.resource_show,
        }

    # IResourceController

    def before_update(self, context, obj, *args, **kwargs):
        resource = toolkit.get_action('resource_show')(context, obj)
        helpers.is_protected(resource, action='update')

    def before_delete(self, context, obj, *args, **kwargs):
        resource = toolkit.get_action('resource_show')(context, obj)
        helpers.is_protected(resource, action='delete')

    # IRouters

    def after_map(self, _map):
        with routes.mapper.SubMapper(_map, controller='ckanext.coat.controller:VersionController') as m:
            m.connect('dataset.new_version', '/dataset/{uid}/new_version', action='new_version')
            m.connect('dataset.zip', '/dataset/{uid}/zip', action='zip')
        return _map
