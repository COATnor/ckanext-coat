import ckan.plugins.toolkit as toolkit
from ckan.logic.action.update import package_update as ckan_package_update
from ckanext.coat import helpers


@toolkit.side_effect_free
def package_update(context, data_dict):
    package = toolkit.get_action('package_show')(context, data_dict)
    # check if protected only if not switching between private and public
    if data_dict.get('private', False) == package.get('private', False):
        helpers.is_protected(package)
    return ckan_package_update(context, data_dict)
