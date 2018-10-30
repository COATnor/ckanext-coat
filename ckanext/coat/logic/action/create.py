import ckan.plugins.toolkit as toolkit
from ckan.logic.action.create import package_create as ckan_package_create


@toolkit.side_effect_free
def package_create(context, data_dict):
    if len(data_dict) <= 3:
        return ckan_package_create(context, data_dict)
    base_name = data_dict['name']
    data_dict.setdefault('extras', [])
    data_dict['extras'].append(
        {'key': 'base_name', 'value': base_name},
    )
    if not data_dict.get('version', False):
        response = toolkit.get_action('package_search')(
            context, {'fq_list': ['base_name:"%s"' % base_name]})
        if response.get('results', []):
            latest = response['results'][0]
            try:
                version = str(int(latest['version'])+1)
            except ValueError:
                version = '1'
            data_dict['version'] = version
        else:
            data_dict['version'] = '1'
    data_dict['name'] += '_v' + data_dict['version']
    package = ckan_package_create(context, data_dict)
    toolkit.get_action('dataset_version_create')(
        context, {
            'id': package['id'],
            'base_name': base_name,
            'owner_org': data_dict['owner_org'],
        }
    )
    return package
