import ckanext.coat.logic.utils as utils
from ckan.logic.action.update import package_update as ckan_package_update
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic

import pathlib

@toolkit.side_effect_free
def package_update(context, data_dict):
    package_old = toolkit.get_action('package_show')(context, data_dict)
    package_new = ckan_package_update(context, data_dict)
    if utils.is_mirrored(context, data_dict):
        return package_new
    if (package_old.get('state', '').startswith('draft') and
        package_new.get('state') == 'active' and
        package_new['version']) or \
       (package_old['version'] != package_new['version']):
        dst_path = utils.get_dst_path(context, package_new)
        utils.new_release(dst_path, package_new['version'])
        utils.sync(context, package_new)
    return package_new
