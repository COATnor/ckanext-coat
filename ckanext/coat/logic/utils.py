import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckan.lib.helpers import url_for
import ckan.common

import copy
import datetime
import os
import pathlib
import shutil
import six

def copytree_hard(src, dst):
    if six.PY3:
        shutil.copytree(src, dst, copy_function=os.link)
    else:
        os.system("cp -Rl %s %s" % (src, dst))

storage_path = pathlib.Path(ckan.common.config.get('ckan.storage_path'))
archive_path = storage_path / 'archive'

def get_extra(pkg, value, default=None):
    if 'extras' in pkg:
        extras = {d['key']: d['value'] for d in pkg['extras']}
        return extras.get(value, default)
    return default

def is_resource(obj):
    return 'package_id' in obj

def get_dst_path(context, obj):
    if is_resource(obj):
        params = {'id': obj['package_id']}
        package = toolkit.get_action('package_show')(context, params)
    else:
        package = obj
    return archive_path / package['name'] / 'latest'

def get_src_dst(context, obj):
    file_name = obj['name']
    dst_path = get_dst_path(context, obj)
    upload = uploader.get_resource_uploader(obj)
    src = pathlib.Path(upload.get_path(obj['id']))
    dst = dst_path / file_name
    return src, dst

def new_revision(dst_path):
    timestamp = datetime.datetime.now().isoformat()
    rev_path = dst_path / '..' / 'revisions' / timestamp
    copytree_hard(dst_path, rev_path)

def new_release(dst_path, version):
    rel_path = dst_path / '..' / 'releases' / version
    copytree_hard(dst_path, rel_path)

def get_package_from_resource(context, obj):
    return toolkit.get_action('package_show')(context, {'id':obj['package_id']})

def is_mirrored(context, obj):
    if is_resource(obj):
        pkg = get_package_from_resource(context, obj)
    else:
        pkg = obj
    return get_extra(pkg, 'mirrored')

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

def sync(context, package_new):
    # Syncronize the public dataset

    public_name = get_extra(package_new, 'push_releases_to')
    if not public_name or public_name == package_new['name']:
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
        if key in public_dict:
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
    src_path = archive_path / package_new['name'] / 'releases' / package_new['version']
    dst_path = get_dst_path(context, public)
    shutil.rmtree(str(dst_path), ignore_errors=True)
    copytree_hard(str(src_path), str(dst_path))
    new_release(dst_path, public['version'])
    if 'resources' not in package_new:
        package_new['resources'] = []
    for original_resource in package_new['resources']:
        resource = copy.deepcopy(original_resource)
        for key in ('id', 'revision_id',):
            if key in resource:
                del resource[key]
        if resource.get('url_type') == 'upload':
            path = 'releases/%s/%s' % (public['version'], resource['name'])
            url = url_for('dataset.download', uid=package_new['name'], path=path, qualified=True)
            resource.update({
                'url_type': None,
                'url': url,
            })
        resource['package_id'] = public['id']
        toolkit.get_action('resource_create')(context, resource)
