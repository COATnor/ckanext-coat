import ckan.plugins.toolkit as toolkit
from ckan.logic.action.create import package_create as ckan_package_create


@toolkit.side_effect_free
def package_create(context, data_dict):
    package = ckan_package_create(context, data_dict)
    if 'extras' not in data_dict:
        return package  # saving meta-dataset
    extras = {item['key']: item['value'] for item in data_dict['extras']}
    if 'base_name' in extras:
        toolkit.get_action('dataset_version_create')(
            context, {
                'id': package['id'],
                'base_name': extras['base_name'],
                'owner_org': data_dict['owner_org'],
            }
        )
    return package
