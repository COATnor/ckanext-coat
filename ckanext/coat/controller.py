import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model
import ckan.lib.base as base
import ckan.lib.helpers as h
from ckan.common import _, request, response, c
from ckanext.coat.helpers import extras_dict, new_context, next_version, get_resource_path
from ckanext.datasetversions.helpers import get_context
from ckan.controllers.package import PackageController

import paste.fileapp

import copy
import datetime
import mimetypes
import tempfile
import os
import zipfile


def increment_download_counter(context, resource_uid):
    resource = toolkit.get_action('resource_show')(context, {'id': resource_uid})
    ### the code below executed if there is no permission error
    resource['downloads'] = str(int(resource.get('downloads', '0'))+1)
    # disable before_update checks like is_protected
    resource['__force'] = True
    # allow to update the resource even if the user cannot modify it
    #   so downloads can be incremented
    context['ignore_auth'] = True
    toolkit.get_action('resource_update')(context, resource)
    return resource['downloads']


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

        # remove also doi entry:
        for key in ('doi', 'doi_date_published', 'doi_publisher', 'doi_status'):
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
            #import pdb;pdb.set_trace()
            for key in ('id', 'revision_id'):
                if key in resource:
                    del resource[key]
            # modify the new resource
            resource['package_id'] = package_new['id']
            if resource['url_type'] != 'upload':
                resource['url'] = resource['name']
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

        # Similar to custom_resource_download
        package['downloads'] = str(int(package.get('downloads', '0'))+1)
        context['ignore_auth'] = True
        toolkit.get_action('package_update')(context, package)

        for resource in package['resources']:
            increment_download_counter(context, resource['id'])

        return self._send_file(zip_path, '%s.zip' % uid)


class CustomPackageController(PackageController):
    def custom_resource_download(self, uid, resource_uid, filename=None):
        response = self.resource_download(uid, resource_uid, filename)
        ### the code below executed if there is no errors such as missing file
        ###   or redirect - uploaded file only are available for download
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj}
        increment_download_counter(context, resource_uid)
        return response
