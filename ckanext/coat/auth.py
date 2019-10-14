import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import helpers as h
from datetime import datetime

def embargo_access(context, data_dict=None):
    package = h.get_package(data_dict)
    try:
        toolkit.check_access('package_update', context, package)
    except logic.NotAuthorized:
        embargo = h.extras_dict(package).get('embargo', None)
        if embargo == "2-years":
            embargo_date = h.extras_dict(package).get('embargo_date', None)
            try:
                #if datetime.now() < datetime.strptime(embargo_date, '%Y-%m-%d'):
                if datetime.now() < embargo_date:
                    raise toolkit.NotAuthorized, 'The dataset is under embargo until %s.' % embargo_date
            except ValueError:
                pass  # warning
        elif embargo == 'hidden':
            raise toolkit.NotAuthorized, 'The dataset is private'



