import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import helpers as h
from datetime import datetime

def embargo_access(context, data_dict):
    package = h.get_package(data_dict, context)
    embargo = package.get('embargo', None)
    if embargo:
        try:
            toolkit.check_access('package_update', context, package)
        except logic.NotAuthorized:
            try:
                if datetime.now() < datetime.strptime(embargo, '%Y-%m-%d'):
                    raise toolkit.NotAuthorized, 'The dataset is under embargo until %s.' % embargo
            except ValueError:
                pass # warning
