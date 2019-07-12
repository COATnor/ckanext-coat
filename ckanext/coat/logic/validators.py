from ckan.plugins.toolkit import Invalid
import ckan.plugins.toolkit as toolkit

def resource_name_conflict(obj, context):
    pkg_dict = toolkit.get_action('package_show')(
        context, {'id': obj['package_id']})
    for resource in pkg_dict['resources']:
        if resource['name'] == obj['name']:
            raise Invalid('Resource with the same name in the same' \
                'dataset already exists: %s' % obj['name'])
    return True
