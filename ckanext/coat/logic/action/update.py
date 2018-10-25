import ckan.plugins.toolkit as toolkit
from ckan.logic.action.update import package_update as ckan_package_update


@toolkit.side_effect_free
def package_update(context, data_dict):
    package = toolkit.get_action('package_show')(context, data_dict)
    data_dict['name'] = data_dict['name'].rsplit(package['version'], 1)[0]
    data_dict['name'] += data_dict['version']
    return ckan_package_update(context, data_dict)
