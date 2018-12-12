import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
from ckan.common import _
from ckanext.coat.helpers import extras_dict, new_context
from ckanext.datasetversions.helpers import get_context

import copy
import datetime


class VersionController(toolkit.BaseController):
    def new_version(self, uid):
        context = new_context()
        data_dict = {'id': uid}

        # check if package exists
        try:
            package = toolkit.get_action('package_show')(context, data_dict)
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Dataset not found'))

        resources = package['resources']
        context = get_context(context)  # needed ?

        # remove references to the original package
        for key in ('id', 'revision_id'):
            if key in package:
                del package[key]

        # update the new package values
        package.update({
            'resources': [],
            'metadata_created': datetime.datetime.now(),
            'medatata_modified': datetime.datetime.now(),
            'name': extras_dict(package)['base_name'],
            'version': str(int(package.get('version', '0'))+1),
        })

        # save the package
        package_new = toolkit.get_action('package_create')(context, package)

        # populate the new package with the old resources
        for original_resource in resources:
            # clone the resource
            resource = copy.deepcopy(original_resource)
            for key in ('id', 'revision_id'):
                if key in resource:
                    del resource[key]
            # modify the new resource
            resource.update({
                'package_id': package_new['id'],
                'url_type': 'url_to_resource',  # link, not upload file field
            })
            toolkit.get_action('resource_create')(context, resource)

        h.redirect_to(controller='package', action='read', id=package_new['id'])  # not working
