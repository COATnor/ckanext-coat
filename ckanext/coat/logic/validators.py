from ckan.plugins.toolkit import Invalid

def resource_name_conflict(value, context):

    model = context['model']
    session = context['session']

    result = session.query(model.Resource).filter_by(name=value).first()

    if result:
        raise Invalid(('Resource with the same name already exists') + ': %s' % value)
    return value
