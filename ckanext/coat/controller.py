import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
from ckan.common import c, _
from ckanext.coat.helpers import extras_dict
from ckanext.datasetversions.helpers import get_context

import datetime


class VersionController(toolkit.BaseController):
    def new_version(self, uid):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': uid}

        # check if package exists
        try:
            package = toolkit.get_action('package_show')(context, data_dict)
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Dataset not found'))

        # Remove references to the original package
        del package['id']
        del package['revision_id']
        context = get_context(context)

        package['metadata_created'] = datetime.datetime.now()
        package['metadata_modified'] = package['metadata_created']
        package['name'] = extras_dict(package)['base_name']
        package['version'] = str(int(package.get('version', "0"))+1)
        package_new = toolkit.get_action('package_create')(context, package)
        h.redirect_to(controller='package', action='edit', id=package_new['id'])
