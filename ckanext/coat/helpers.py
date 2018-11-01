def extras_dict(package):
    return {f['key']:f['value'] for f in package['extras']}
