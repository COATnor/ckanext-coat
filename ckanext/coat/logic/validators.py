from ckan.plugins.toolkit import Invalid
import ckan.plugins.toolkit as toolkit
from ckanext.coat.helpers import extras_dict

def resource_name_conflict_global(context, pkg_dict, name):
    model = context['model']
    session = context['session']
    extras = extras_dict(pkg_dict)
    result = session.query(model.Package) \
        .join(model.PackageExtra,
            model.PackageExtra.package_id == model.Package.id) \
        .join(model.Resource,
            model.Resource.package_id == model.Package.id) \
        .filter(
            model.PackageExtra.key == 'base_name',
            model.PackageExtra.value != extras['base_name'],
            model.Resource.name.ilike(name),
        ).first()
    if result:
        raise Invalid('Resource with the same name already exists: ' + name)

def resource_name_conflict_local(context, pkg_dict, name):
    for resource in pkg_dict['resources']:
        if resource['name'].lower() == name.lower():
            raise Invalid('Resource with the same name in the same ' \
                          'dataset already exists: ' + name)

def resource_name_conflict(context, obj, globally_unique):
    pkg_dict = toolkit.get_action('package_show')(
        context, {'id': obj['package_id']})
    name = obj['name']
    resource_name_conflict_local(context, pkg_dict, name)
    if globally_unique:
        resource_name_conflict_global(context, pkg_dict, name)
    return name
