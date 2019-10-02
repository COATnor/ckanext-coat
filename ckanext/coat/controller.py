import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
from ckan.common import _, request, response
from ckanext.coat.helpers import extras_dict, new_context, next_version, get_resource_path
from ckanext.datasetversions.helpers import get_context

import paste.fileapp

import copy
import datetime
import mimetypes
import tempfile
import os
import zipfile


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
        base_name = extras_dict(package)['base_name']
        package.update({
            'resources': [],
            'metadata_created': datetime.datetime.now(),
            'medatata_modified': datetime.datetime.now(),
            'name': base_name,
            'private': True,
            'version': next_version(package),
        })

        # save the package
        package_new = toolkit.get_action('package_create')(context, package)

        # populate the new package with the old resources
        for original_resource in resources:
            # clone the resource
            resource = copy.deepcopy(original_resource)
            for key in ('id', 'revision_id', 'url'):
                if key in resource:
                    del resource[key]
            # modify the new resource
            resource.update({
                'package_id': package_new['id'],
                'url': resource['name'],
            })
            resource_new = toolkit.get_action('resource_create')(context, resource)
            # avoid hardlinking when cloning link resources
            if resource['url_type'] != "upload":
                continue
            src = get_resource_path(original_resource)
            dst = get_resource_path(resource_new)
            dst_dir = os.path.dirname(dst)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            os.link(src, dst)

        h.redirect_to(controller='package', action='read', id=base_name)

    def _send_file(self, path, name):
        # Similar to resource_download from ckan/controllers/package.py
        fileapp = paste.fileapp.FileApp(path)
        try:
            status, headers, app_iter = request.call_application(fileapp)
        except OSError:
            base.abort(404, _('Resource data not found'))
        response.headers.update(dict(headers))
        content_type, content_enc = mimetypes.guess_type(path)
        if content_type:
            response.headers['Content-Type'] = content_type
            response.status = status
        response.headers['Content-Disposition'] = 'attachment; filename="%s"' % name
        # FILESIZE MISSING
        return app_iter

    def zip(self, uid):
        context = new_context()
        data_dict = {'id': uid}

        # check if package exists
        try:
            package = toolkit.get_action('package_show')(context, data_dict)
            toolkit.get_action('resource_show')(context, package['resources'][0])
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Dataset not found'))

        zip_path = os.path.join(tempfile.gettempdir(), package['id']+'.zip')
        with zipfile.ZipFile(zip_path, 'w') as archive:
            for resource in package['resources']:
                if resource['url_type'] != 'upload':
                    continue
                path = get_resource_path(resource)
                archive.write(path, resource['name'])

        return self._send_file(zip_path, '%s.zip' % uid)
