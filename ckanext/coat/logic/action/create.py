import ckan.plugins.toolkit as toolkit
from ckan.logic.action.create import package_create as ckan_package_create
from ckanext.coat.helpers import extras_dict

@toolkit.side_effect_free
def package_create(context, data_dict):
    # parent dataset
    # https://github.com/aptivate/ckanext-datasetversions/issues/10
    if len(data_dict) <= 3:
        return ckan_package_create(context, data_dict)

    # set base_name extra field
    base_name = data_dict['name']
    data_dict.setdefault('extras', [])
    if 'base_name' not in extras_dict(data_dict):
        data_dict['extras'].append(
            {'key': 'base_name', 'value': base_name},
         )

    # set version
    if not data_dict.get('version', False):
        response = toolkit.get_action('package_search')(
            context, {'q': 'base_name:"%s"' % base_name})
        if response['count'] > 0:
            version = response['results'][0].get('version', '1')
            if version.isdigit():
                data_dict['version'] = str(int(version)+1)
            else:
                data_dict['version'] = '1'
        else:
            data_dict['version'] = '1'

    # append version to the name (it has to be unique)
    data_dict['name'] += '_v' + data_dict['version']

    # create package and version
    package = ckan_package_create(context, data_dict)
    toolkit.get_action('dataset_version_create')(
        context, {
            'id': package['id'],
            'base_name': base_name,
            'owner_org': data_dict['owner_org'],
        }
    )

    return package
