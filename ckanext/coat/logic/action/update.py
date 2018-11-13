import ckanext.coat.logic.git_archive as git_archive
from ckan.logic.action.update import package_update as ckan_package_update
import ckan.plugins.toolkit as toolkit

@toolkit.side_effect_free
def package_update(context, data_dict):
    package = toolkit.get_action('package_show')(context, data_dict)
    ckan_package_update(context, data_dict)
    if package['version'] != data_dict['version']:
        directory = git_archive.get_directory(context, package)
        git_archive.set_author(context, obj, directory)
        git_archive.new_release(obj, directory)
