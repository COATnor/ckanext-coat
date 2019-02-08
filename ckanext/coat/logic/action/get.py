import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
from ckan.logic.action.get import package_search as ckan_package_search
from ckan.logic.action.get import resource_show as ckan_resource_show
from ckanext.coat import auth

@toolkit.side_effect_free
def package_search(context, data_dict):
    data_dict['fq_list'] = [
        '{!collapse field=base_name max=field(version_i)}',
    ]
    return ckan_package_search(context, data_dict)

@toolkit.chained_action
def package_show(original_action, context, data_dict):
    package = original_action(context, data_dict)
    try:
        auth.embargo_access(context, data_dict)
    except logic.NotAuthorized:
        for resource in package['resources']:
            resource['url'] = "#resource-under-embargo"
    return package

@toolkit.side_effect_free
def resource_show(context, data_dict):
    auth.embargo_access(context, data_dict)
    return ckan_resource_show(context, data_dict)
