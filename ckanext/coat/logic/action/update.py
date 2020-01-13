import ckan.plugins.toolkit as toolkit
from ckan.logic.action.update import package_update as ckan_package_update
from ckanext.coat.helpers import extras_dict, is_protected


@toolkit.side_effect_free
def package_update(context, data_dict):
    package = toolkit.get_action('package_show')(context, data_dict)
    # check if protected only if not switching between private and public
    if data_dict.get('private', False) == package.get('private', False):
        if not context.get('ignore_auth', False):
           is_protected(package)

    # ckanext-scheming workaround
    base_name = extras_dict(package).get('base_name')
    if base_name:
        data_dict.setdefault('extras', [])
        if 'base_name' not in extras_dict(data_dict):
            data_dict['extras'].append(
                {'key': 'base_name', 'value': base_name},
             )

    return ckan_package_update(context, data_dict)
