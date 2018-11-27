import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import routes.mapper
import ckanext.coat.logic.utils as utils
import ckanext.coat.logic.action.update

import os

class CoatPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'coat')

    # IPackageController / IResourceController

    def after_create(self, context, obj):
        dst_path = utils.get_dst_path(context, obj)
        if utils.is_resource(obj):
            if obj.get('url_type') != 'upload':
                return
            src, dst = utils.get_src_dst(context, obj)
            os.link(str(src), str(dst))
        else:
            rev_path = dst_path / '..' / 'revisions'
            rel_path = dst_path / '..' / 'releases'
            os.makedirs(str(dst_path))
            os.makedirs(str(rev_path))
            os.makedirs(str(rel_path))
        utils.new_revision(dst_path)

    def after_update(self, context, obj):
        if utils.is_resource(obj):
            self.after_create(context, obj)
        else:
            pass

    def before_delete(self, context, uid, objs):
        for obj in objs:
            dst_path = utils.get_dst_path(context, obj)
            if utils.is_resource(obj):
                src, dst = utils.get_src_dst(context, obj)
                if dst.is_file():
                    os.remove(str(dst))
                utils.new_revision(dst_path)
            else:
                pass # empty repo?

    # IActions

    def get_actions(self):
        return {
            'ckan_package_update':
            ckanext.coat.logic.action.update.ckan_package_update,
            'package_update':
            ckanext.coat.logic.action.update.package_update,
        }

    # IRoutes

    def before_map(self, routes_map):
        controller = 'ckanext.coat.controllers:ArchiveController'
        with routes.mapper.SubMapper(routes_map, controller=controller) as m:
            m.connect('dataset.revisions', '/dataset/{uid}/revisions', action='revisions')
            m.connect('dataset.download', '/dataset/{uid}/{path:.*?}/download', action='download')
        return routes_map
