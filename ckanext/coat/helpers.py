import ckan.logic as logic
import ckan.model as model
from ckan.common import g
import ckan.plugins.toolkit as toolkit
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
    return package.get('private', False)

def is_protected(obj):
    package = get_package(obj)
    if is_old(package):
        raise logic.NotAuthorized
