import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckanext.coat.helpers as h

def embargo_access(context, data_dict=None):
    package = h.get_package(data_dict)
    try:
        toolkit.check_access('package_update', context, package)
    except logic.NotAuthorized:
        embargo = h.extras_dict(package).get_default('embargo', None)
        if embargo:
            try:
                if time.time() < time.strptime(embargo, '%Y-%m-%d'):
                    return {'success': False,
                            'msg':'The dataset is under embargo until %s.' % embargo}
            except ValueError:
                pass # warning
    return {'success': True}
