import ckanext.coat.logic.utils as utils
from ckan.logic.action.update import package_update as ckan_package_update
import ckan.plugins.toolkit as toolkit

@toolkit.side_effect_free
def package_update(context, data_dict):
    package_old = toolkit.get_action('package_show')(context, data_dict)
    package_new = ckan_package_update(context, data_dict)
    if package_old['version'] != package_new['version']:
        dst_path = utils.get_dst_path(context, package_new)
        utils.new_release(dst_path, package_new['version'])
    return package_new
