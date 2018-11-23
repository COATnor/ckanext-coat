import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
import ckan.common

import datetime
import os
import pathlib
import shutil
import six

def copytree_hard(src, dst):
    if six.PY3:
        shutil.copytree(src, dst, copy_function=os.link)
    else:
        os.system("cp -Rl %s %s" % (src, dst))

storage_path = pathlib.Path(ckan.common.config.get('ckan.storage_path'))
archive_path = storage_path / 'archive'

def is_resource(obj):
    return 'package_id' in obj

def get_dst_path(context, obj):
    if is_resource(obj):
        params = {'id': obj['package_id']}
        package = toolkit.get_action('package_show')(context, params)
    else:
        package = obj
    return archive_path / package['name'] / 'latest'

def get_src_dst(context, obj):
    file_name = obj['name']
    dst_path = get_dst_path(context, obj)
    upload = uploader.get_resource_uploader(obj)
    src = pathlib.Path(upload.get_path(obj['id']))
    dst = dst_path / file_name
    return src, dst

def new_revision(dst_path):
    timestamp = datetime.datetime.now().isoformat()
    rev_path = dst_path / '..' / 'revisions' / timestamp
    copytree_hard(dst_path, rev_path)

def new_release(dst_path, version):
    rel_path = dst_path / '..' / 'releases' / version
    copytree_hard(dst_path, rel_path)
