# -*- coding: UTF-8 -*-

from django.contrib.sites.models import Site
from urlparse import urljoin
from django.conf import settings
import os
import commands
import hashlib

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("django")


def parse_to_url_https(obj):
    return parse_to_url(obj, "https")


def parse_to_url_http(obj):
    return parse_to_url(obj, "http")


def parse_to_url(obj, pre):
    # Site.objects.clear_cache()

    current_site = Site.objects.get_current()

    root_url = '%s://%s' % (pre, current_site.domain)

    return urljoin(
        root_url,
        str(obj)
    )


# def remote_app_url(pa, pre, obj):
#     file_dir = "default"
#     app_group_name = obj.mobile_application.mobile_application_group.type
#     logger.info("get remote app url object in group:" + app_group_name)
#
#     if len(app_group_name) > 0:
#         file_dir = app_group_name
#
#     return remote_url(pa, pre, obj, file_dir)
#
#
# def remote_url(pa, pre, obj, file_dir):
#     def get_filename(path):
#         return os.path.basename(path)
#
#     the_file_name = get_filename(pa)
#
#     root_url = '%s://%s%s%s/%s' % (pre,
#                                    settings.REMOTE_FILE_ACCESS__DOMAIN,
#                                    settings.REMOTE_FILE_ACCESS_BASE,
#                                    file_dir,
#                                    the_file_name)
#
#     logger.info("get remote url:" + root_url)
#
#     return root_url
#
#
# def send_app_file_to_remote_server(obj):
#     logger.info("begin execute send_app_file_to_remote_server method.")
#     logger.info(obj.path.file)
#     logger.info(obj.path.url)
#
#     file_dir = "default"
#     app_group_name = obj.mobile_application.mobile_application_group.type
#     logger.info("get send file object in group:" + app_group_name)
#
#     if len(app_group_name) > 0:
#         file_dir = app_group_name
#
#     return send_file_to_remote_server(obj, file_dir)
#
#
# def send_file_to_remote_server_by_path(full_path, file_dir):
#     logger.info("begin execute send_file_to_remote_server method.")
#
#     # 修改文件权限
#     chmod = "chmod 644 %s" % full_path
#     logger.info("modify file visit permission :" + chmod)
#
#     chd_status, chd_output = commands.getstatusoutput(chmod)
#     if chd_status == 0:
#         logger.info("modify file permissions is 644")
#     else:
#         logger.info(chd_output)
#
#     # 创建文件夹
#     cmd_mk_dir = "ssh root@%s 'mkdir %s%s ' " % (settings.REMOTE_IP, settings.REMOTE_FILE_PATH, file_dir)
#     chd_status, chd_output = commands.getstatusoutput(cmd_mk_dir)
#     if chd_status == 0:
#         logger.info("make dir in root remote success")
#     else:
#         logger.info(chd_output)
#
#     # -e ssh -p 21022 移除端口
#
#     comm = "rsync -auz  -e ssh --progress %s  root@%s:%s%s" % (full_path,
#                                                                settings.REMOTE_IP,
#                                                                settings.REMOTE_FILE_PATH,
#                                                                file_dir)
#
#     logger.info("send file to remote server  is :" + comm)
#
#     status, output = commands.getstatusoutput(comm)
#
#     if status == 0:
#         logger.info("file upload load success")
#     else:
#         logger.info(output)
#
#     return status, output
#
#
# def send_file_to_remote_server(obj, file_dir):
#     logger.info(obj.path.file)
#     logger.info(obj.path.url)
#
#     # def get_file_dir(path):
#     #     return os.path.dirname(path)
#
#     # fullDir = settings.FILE_HOME + get_file_dir(obj.path.url)
#     full_path = settings.FILE_HOME + obj.path.url
#
#     return send_file_to_remote_server_by_path(full_path=full_path, file_dir=file_dir)
#
#
# def send_patch_file_to_remote_server(path, file_dir):
#     logger.info(path)
#
#     full_path = settings.FILE_HOME + path
#
#     return send_file_to_remote_server_by_path(full_path=full_path, file_dir=file_dir)
#
#
# def rm_file_to_remote_server(filename, file_dir):
#     logger.info("begin execute rm_file_to_remote_server method.")
#
#     # ssh username@domain.com 'rm /some/where/some_file.war'
#     comm = "ssh root@%s rm -rf %s%s/%s" % (settings.REMOTE_IP, settings.REMOTE_FILE_PATH, file_dir, filename)
#
#     logger.info("remove file on remote server  is :" + comm)
#
#     status, output = commands.getstatusoutput(comm)
#
#     if status == 0:
#         logger.info("file upload load success")
#     else:
#         logger.info(output)
#
#     return status, output


def md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# hash_md5 = md5("/Users/caiwenshu/Desktop/bsdiff-4.3/old-to-new.patch")
# print hash_md5
