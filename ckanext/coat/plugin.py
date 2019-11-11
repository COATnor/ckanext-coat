from ckan.common import config
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.coat.logic.action.create
import ckanext.coat.logic.action.get
import ckanext.coat.logic.action.update
import ckanext.coat.logic.action.delete
import ckanext.coat.logic.validators as validators
import ckanext.coat.auth as auth
from ckanext.coat import helpers
import ckan.lib.base as base
import routes.mapper

import requests

CKAN_SCHEMA = 'http://solr:8983/solr/ckan/schema'

class CoatPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)

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

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'coat_is_under_embargo': helpers.is_under_embargo,
        }

    # IDatasetForm

    def _custom_package_schema(self, schema):
        validators = schema['resources']['name']
        for validator in ('lowercase_extension', 'resource_name_conflict'):
            validators.append(toolkit.get_validator(validator))
        schema['resources']['name'] = validators
        return schema

    def create_package_schema(self):
        schema = super(CoatPlugin, self).create_package_schema()
        schema['private'].append(toolkit.get_validator('private_on_creation'))
        return self._custom_package_schema(schema)

    def update_package_schema(self):
        schema = super(CoatPlugin, self).update_package_schema()
        return self._custom_package_schema(schema)

    def show_package_schema(self):
        schema = super(CoatPlugin, self).show_package_schema()
        return schema

    def is_fallback(self):
        return False

    def package_types(self):
        if config.get('ckanext.coat.custom_form', "true").lower() == "false":
            return []
        else:
            return ['dataset']


    # IValidators

    def get_validators(self):
        return {
            'lowercase_extension': validators.lowercase_extension,
            'resource_name_conflict': validators.resource_name_conflict,
            'private_on_creation': validators.private_on_creation,
        }
