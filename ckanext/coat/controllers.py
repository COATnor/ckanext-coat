from ckan.common import _, c, config, request, response
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.plugins import toolkit

import paste.fileapp

import pathlib
import mimetypes

# duplicated definition
storage_path = pathlib.Path(config.get('ckan.storage_path'))
archive_path = storage_path / 'archive'

class ArchiveController(toolkit.BaseController):
    def _get_revisions(self, uid):
        revisions = []
        directories = list((archive_path / uid).glob('revisions/*/'))
        directories.sort(reverse=True)
        for directory in directories:
            relative = directory.relative_to(archive_path)
            files = []
            for obj in directory.glob('*'):
                files.append({
                    'name': obj.name,
                    'url': '%s/download' % obj.relative_to(archive_path),
                })
            revisions.append({
                'name': directory.name,
                'files': files,
                'url': relative,
                'private': True,
            })
        return revisions

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
        return base.render(template, extra_vars={
            'pkg_dict': pkg_dict,
            'revisions': self._get_revisions(uid),
        })

    def download(self, uid, path):
        pkg, pkg_dict = self._get_dataset(uid)  # check for permissions
        fullpath = str(archive_path / uid / path)
        # Similar to resource_download from ckan/controllers/package.py
        fileapp = paste.fileapp.FileApp(fullpath)
        try:
            status, headers, app_iter = request.call_application(fileapp)
        except OSError:
            base.abort(404, _('Resource data not found'))
        response.headers.update(dict(headers))
        content_type, content_enc = mimetypes.guess_type(path)
        if content_type:
            response.headers['Content-Type'] = content_type
            response.status = status
        response.headers['Content-Disposition'] = 'attachment; filename="%s"' % pathlib.Path(path).name
        return app_iter
