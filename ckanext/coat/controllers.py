from ckan.common import _, c, config, request, response
from ckan.lib import helpers
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.plugins import toolkit

import paste.fileapp

import pathlib

import datetime
import mimetypes
import os.path
import shutil
import tempfile

# duplicated definition
storage_path = pathlib.Path(config.get('ckan.storage_path'))
archive_path = storage_path / 'archive'

class ArchiveController(toolkit.BaseController):
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
        return app_iter
        # FILESIZE MISSING

    def _get_versions(self, uid, directories=[]):
        base = archive_path / uid
        versions = []
        for absolute_path in base.glob('*/*'):
            path = absolute_path.relative_to(base)
            directory, name = str(path).split('/')
            if directory not in directories:
                continue
            files = []
            for filepath in absolute_path.glob('*'):
                files.append(filepath.relative_to(base))
            mtime = os.path.getmtime(str(absolute_path))
            mtime = datetime.datetime.fromtimestamp(mtime)
            versions.append({
                'directory': directory,
                'files': files,
                'path': path,
                'name': name,
                'mtime': mtime,
            })
        versions.sort(key=lambda v: v['mtime'], reverse=True)
        return versions

    def _get_dataset(self, uid):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': uid, 'include_tracking': True}
        try:
            pkg_dict = toolkit.get_action('package_show')(context, data_dict)
            pkg = context['package']
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Dataset not found'))
        return pkg, pkg_dict

    def index(self, uid):
        pkg, pkg_dict = self._get_dataset(uid)
        template = "package/archive_index.html"
        directories = ["revisions", "releases"]
        return base.render(template, extra_vars={
            'pkg_dict': pkg_dict,
            'versions': self._get_versions(uid, directories),
            'h': helpers,
        })

    def download(self, uid, path):
        pkg, pkg_dict = self._get_dataset(uid)  # check for permissions
        fullpath = str(archive_path / uid / path)
        return self._send_file(fullpath, pathlib.Path(path).name)

    def compress(self, uid, directory, version, compression):
        pkg, pkg_dict = self._get_dataset(uid)  # check for permissions
        extension = {
            'zip': '.zip',
            'gztar': '.tar.gz',
            'bztar': '.tar.bz2',
        }[compression]
        path = str(archive_path / uid / directory / version)
        with tempfile.NamedTemporaryFile() as fp:
            shutil.make_archive(fp.name, compression, path)  # Python < 3.4 max 2 GB
            return self._send_file(fp.name+extension, '%s-%s%s' % (uid, version, extension))
            # REMOVE THE ZIP FILE!
