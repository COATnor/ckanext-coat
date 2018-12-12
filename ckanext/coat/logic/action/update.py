import ckan.plugins.toolkit as toolkit
from ckan.logic.action.update import package_update as ckan_package_update
from ckanext.coat import helpers


@toolkit.side_effect_free
def package_update(context, data_dict):
    package = toolkit.get_action('package_show')(context, data_dict)
    helpers.check_if_protected(package)
    return ckan_package_update(context, data_dict)
