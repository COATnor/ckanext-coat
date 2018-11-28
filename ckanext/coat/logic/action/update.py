import ckanext.coat.logic.utils as utils
from ckan.logic.action.update import package_update as ckan_package_update
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic

import pathlib

import copy

def get_context(context):  # from ckanext/datasetversions/helpers.py
    """An internal context generator. Accepts a CKAN context.
    CKAN's internals put various things into the context which
    makes reusing it for multiple API calls inadvisable. This
    function adds more fine grain control on the context from
    our plugin logic side.
    """
    new_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context.get('user'),
        'ignore_auth': context.get('ignore_auth', False),
        'use_cache': context.get('use_cache', False),
    }

    if 'validate' in context:
        new_context['validate'] = context['validate']

    return new_context

@toolkit.side_effect_free
def package_update(context, data_dict):
    package_old = toolkit.get_action('package_show')(context, data_dict)
    package_new = ckan_package_update(context, data_dict)
    if package_old['version'] == package_new['version']:
        return package_new
    dst_path = utils.get_dst_path(context, package_new)
    utils.new_release(dst_path, package_new['version'])

    # Syncronize the public dataset

    public_name = utils.get_extra(package_new, 'push_releases_to')
    if not public_name:
        return package_new

    public_dict = copy.deepcopy(package_new)
    public_extras = [
        {'key': 'mirrored', 'value': 'true'},
    ]
    for field in package_new['extras']:
        if field['key'] not in ('push_releases_to',):
            public_extras.append(field)

    public_dict.update({
        'name': public_name,
        'title': public_name,
        'private': False,
        'extras': public_extras,
    })
    for key in ('id', 'revision_id',):
        del public_dict[key]

    # needed to cleanup context
    # bad things happens if you comment this line
    context = get_context(context)

    public_pkg = context['model'].Package.get(public_name)
    if public_pkg:
        # https://github.com/ckan/ckan/issues/4565
        public_dict['id'] = public_pkg.id
        public = toolkit.get_action('package_show')(context, public_dict)
        for resource in public['resources']:
            toolkit.get_action('resource_delete')(context, resource)
        public_dict['resources'] = []
        public = toolkit.get_action('package_update')(context, public_dict)
    else:
        public = toolkit.get_action('package_create')(context, public_dict)
    for resource in package_new['resources']:
        if obj.get('url_type') == 'upload':
            url = resource['url']
        else:
            url = pathlib.Path(resource['url'])
            url = url / '../../archive/release' / package_new['version']
            url = url / pathlib.Path(resource['url']).name
        resource.update({
            'package_id': public['id'],
            'url': str(url),
        })
        toolkit.get_action('resource_create')(context, resource)
    return package_new
