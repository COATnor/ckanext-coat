import ckan.plugins.toolkit as toolkit
from ckan.logic.action.get import package_search as ckan_package_search


@toolkit.side_effect_free
def package_search(context, data_dict):
    data_dict['fq_list'] = [
        '{!collapse field=base_name max=version_i}',
    ]
    return ckan_package_search(context, data_dict)
