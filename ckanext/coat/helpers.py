import ckan.lib.base as base
import ckan.model as model
from ckan.common import g
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckanext.datasetversions.helpers import is_old

def is_resource(obj):
    return 'package_id' in obj

def extras_dict(package):
    return {f['key']:f['value'] for f in package['extras']}

def new_context():
    return {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'for_view': True,
        'auth_user_obj': g.userobj,
    }

def get_package(obj):
    if is_resource(obj):
        context = new_context()
        data_dict = {'id': obj['package_id']}
        return toolkit.get_action('package_show')(context, data_dict)
    else:
        return obj

def is_public(package):
    return not package.get('private', False)

def is_protected(obj):
    if is_resource(obj):
        if obj['url_type'] == 'upload':
            raise base.abort(403, 'Cannot modify an uploaded resource: you have to delete it first')
    package = get_package(obj)
    if is_public(package):
        raise base.abort(403, 'Public datasets cannot be modified: make it private if you really need to amend some information')

def next_version(obj):
    version = obj.get('version', '1')
    if version.isdigit():
        version = str(int(version)+1)
    return version

def get_resource_path(res):
    return uploader.get_resource_uploader(res).get_path(res['id'])
