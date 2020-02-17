# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver

import datetime
import uuid

from validators import *
from utils import *
from django.conf import settings
import zfile
import shutil

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("django")


# TODO:改方法暂时并没有真实调用，后续版本支持
def normalize_image_filename(instance, filename):
    # ext = filename.split('.')[-1]

    # 通过group的类型进行文件分类存储
    app_group_name = instance.mobile_application.mobile_application_group.type

    logger.info("get upload file object in group:" + app_group_name)

    time_format = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # print instance
    filename = "%s_%s.png" % (instance.serverVersion, time_format)

    return "%s/%s/%s" % (app_group_name, "app_icons", filename)


def install_package_file_name(instance, filename):
    ext = filename.split('.')[-1]
    # print instance
    # 通过group的类型进行文件分类存储
    app_group_name = instance.mobile_application.mobile_application_group.type

    logger.info("get upload file object in group:" + app_group_name)

    time_format = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = "%s_%s.%s" % ("_".join(instance.serverVersion.split(".")), time_format, ext)

    logger.info("get install package formatter filename:" + filename)

    return "%s/%s/%s" % (app_group_name, "installpackage", filename)


def android_patch_file_name(instance, filename):
    ext = filename.split('.')[-1]
    # print instance
    # 通过group的类型进行文件分类存储
    app_group_name = instance.from_model.mobile_application.mobile_application_group.type

    logger.info("get upload file object in group:" + app_group_name)

    time_format = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = "%s_to_%s_%s.%s" % ("_".join(instance.from_model.serverVersion.split(".")),
                                   "_".join(instance.to_model.serverVersion.split(".")),
                                   time_format,
                                   ext)

    logger.info("get install package formatter filename:" + filename)

    return "%s/%s/%s" % (app_group_name, "android_patch", filename)


TITLE_PLATFORM = (
    (settings.IOS, 'IOS应用'),
    (settings.ANDROID, 'ANDROID应用'),
)


# 项目组定义
class MobileApplicationGroup(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='产品组名')
    createTime = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='产品组唯一标识名')

    class Meta:
        verbose_name = 'Mobile Application Group'
        verbose_name_plural = 'Mobile Application Group'

    def __unicode__(self):
        return self.name + '(' + self.type + ')'


# 移动App项目的约定
class MobileApplication(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='项目名',
        help_text='该名字只用于查看，不做任何实际的使用'
    )

    createTime = models.DateTimeField(auto_now_add=True)

    mobile_application_group = models.ForeignKey(MobileApplicationGroup, related_name='mobile_application_group')

    platform = models.CharField(
        max_length=20,
        choices=TITLE_PLATFORM,
        default='IOS',
        verbose_name='平台')

    bundle_identifier = models.CharField(
        max_length=200,
        verbose_name='Bundle identifier',
        default='',
        help_text='e.g. org.example.app , android is application id'
    )

    class Meta:
        verbose_name = 'Mobile Application'
        verbose_name_plural = ' Mobile Application'

    def __unicode__(self):
        return self.name + '(' + self.bundle_identifier + ')'


class EmailConfiguration(models.Model):
    name = models.CharField(max_length=200, verbose_name='用户名', default='')
    email = models.EmailField(max_length=200, verbose_name='邮件地址', default='')
    environment = models.CharField(max_length=200, verbose_name='环境', default='all')
    mobile_application_group = models.ForeignKey(MobileApplicationGroup, related_name='mobile_application_group_email')

    class Meta:
        verbose_name = 'Mobile Application Group-邮件人员配置'
        verbose_name_plural = 'Mobile Application Group-邮件人员配置'


def download_html_content_file_name(instance, filename):
    ext = filename.split('.')[-1]
    time_format = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # 通过group的类型进行文件分类存储
    app_group_name = instance.mobile_application_group.type

    logger.info("get download upload file object in group:" + app_group_name)

    filename = "%s.%s" % (time_format, ext)

    logger.info("get download html formatter filename:" + filename)

    # print filename
    return "%s/%s/%s/%s" % (app_group_name, "download", time_format, filename)


# 下载页配置
class DownloadPageConfiguration(models.Model):
    name = models.CharField(max_length=200, verbose_name='名称', default='')
    mobile_application_group = models.ForeignKey(MobileApplicationGroup,
                                                 related_name='mobile_application_group_download')
    path = models.FileField(max_length=200,
                            upload_to=download_html_content_file_name,
                            verbose_name='地址',
                            help_text='注意:上传已.zip结尾的压缩包,并且不能存在根目录')
    rootHtml = models.CharField(max_length=200, default="download.html",
                                help_text='该地址设置网页访问的文件名,默认为download.html',
                                verbose_name='访问html')

    isDistribution = models.BooleanField(help_text='设置为发布版本后，会下线同一个group下的已发布版本',
                                         verbose_name='发布版本')

    class Meta:
        verbose_name = 'Mobile Application Group-下载页面配置'
        verbose_name_plural = 'Mobile Application Group-下载页面配置'


class IOSAppInfo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    serverVersion = models.CharField(max_length=200)
    versionCode = models.CharField(max_length=200)
    updateUrl = models.URLField(max_length=200)
    path = models.FileField(max_length=200, upload_to=install_package_file_name, validators=[validate_ipa_extension])
    serviceUpdateMsg = models.TextField(max_length=400)
    fileInfo = models.TextField(max_length=2000, blank=True)
    createTime = models.DateTimeField(auto_now_add=True)
    isDistribution = models.BooleanField()
    size = models.CharField(max_length=200, blank=True)
    size.verbose_name = '文件大小'

    mobile_application = models.ForeignKey(MobileApplication,
                                           related_name='mobile_application_ios',
                                           verbose_name='所属 Mobile Application',
                                           help_text='所属 Mobile Application')

    stableVersion = models.BooleanField(default=False,
                                        verbose_name='稳定版本',
                                        help_text='对应于线上版本的测试版本，'
                                                  '便于查找历史可用的稳定版本'
                                                  '（每次线上发版，请同步勾选一下对应的测试版本的此选项）')

    historyDistribution = models.BooleanField(default=False)
    historyDistribution.help_text = '是否为历史发布的版本'
    historyDistribution.verbose_name = '历史版本'

    serverVersion.verbose_name = '版本号'
    versionCode.verbose_name = '唯一码'
    updateUrl.verbose_name = '升级地址'
    path.verbose_name = 'ipa包地址'
    serviceUpdateMsg.verbose_name = '升级内容'

    isDistribution.help_text = '设置为发布版本后，会下线已存在的发布版本'
    isDistribution.verbose_name = '发布版本'

    isPreDistribution = models.BooleanField(default=False)
    isPreDistribution.help_text = '设置为预发布版本后，可进行灰度控制'
    isPreDistribution.verbose_name = '预发布版本'

    forceOnline = models.BooleanField(default=False)
    forceOnline.help_text = '选中后，会强制设定当前版本为最新版本（包含已升级的版本）'
    forceOnline.verbose_name = '强制上线'

    versionTimestamps = models.CharField(max_length=200, blank=True)
    versionTimestamps.help_text = '版本时间戳，用于测试版，版本控制'
    versionTimestamps.verbose_name = '版本时间戳'

    buildType = models.CharField(max_length=200, blank=True)
    buildType.help_text = '版本构建类型，SIT，UAT， DISTRIBUTION'
    buildType.verbose_name = '构建类型'

    changeLog = models.TextField(max_length=2000, blank=True)
    changeLog.help_text = 'git提交记录'
    changeLog.verbose_name = '代码改动记录'

    gitUrl = models.CharField(max_length=100, blank=True)
    gitUrl.help_text = 'git url'
    gitUrl.verbose_name = 'git url'

    gitBranch = models.CharField(max_length=100, blank=True)
    gitBranch.help_text = 'git分支'
    gitBranch.verbose_name = 'git分支'

    gitCommit = models.CharField(max_length=100, blank=True)
    gitCommit.help_text = 'git提交hashcode'
    gitCommit.verbose_name = 'git commit code'

    jira_project_key = models.CharField(max_length=100, blank=True)
    jira_project_key.help_text = '对应jira项目KEY'
    jira_project_key.verbose_name = '对应jira项目KEY'

    jira_version = models.CharField(max_length=100, blank=True)
    jira_version.help_text = '对应jira版本信息'
    jira_version.verbose_name = '对应jira版本信息'

    isSendRemoteServer = models.BooleanField(default=False)
    isSendRemoteServer.help_text = '是否发送到远程服务器'
    isSendRemoteServer.verbose_name = '发送服务器状态'

    name = models.CharField(max_length=200, verbose_name='App name', default='', editable=False)

    bundle_identifier = models.CharField(
        max_length=200,
        verbose_name='Bundle identifier',
        default='',
        help_text='e.g. org.example.app'
    )
    display_image = models.ImageField(
        upload_to=normalize_image_filename,
        verbose_name='display image',
        default='',
        help_text='60x60 PNG',
        blank=True
    )
    full_size_image = models.ImageField(
        upload_to=normalize_image_filename,
        verbose_name='full size image',
        default='',
        help_text='512x512 PNG',
        blank=True
    )

    def get_qrcode_url(self):
        if not self.path:
            return None

        return parse_to_url_http(reverse('alps:preview_app', kwargs={'app_id': str(self.uuid)}))

    def get_binary_url(self):
        if not self.path:
            return None

        # return remote_app_url(self.path.url, "https", self)
        return parse_to_url_https(self.path.url)

    def get_plist_url(self):
        self.https = parse_to_url_https
        return self.https(reverse('alps:ios_app_plist', kwargs={'app_id': str(self.uuid)}))

    def get_display_image_url(self):
        if not self.display_image:
            return None
        self.http = parse_to_url_http(self.display_image.url)
        return self.http

    def get_full_size_image_url(self):
        if not self.full_size_image:
            return None
        return parse_to_url_http(self.full_size_image.url)

    # def save(self, *args, **kwargs):
    #     parse = checkipa.ParseIPA(self.path.file)
    #     params = {'parse': parse, 'ipa_filename': self.path.name,
    #               'check_udids': False, 'udids': None,
    #               'verbose': False}
    #     return_info = checkipa.process_ipa(params)
    #     desc = return_info['desc']
    #     bundle_identifier = return_info['bundle_identifier']
    #     bundle_name = return_info['bundle_name']
    #     version = return_info['version']
    #
    #     if bundle_name:
    #         self.name = bundle_name
    #     if version:
    #         self.serverVersion = version
    #
    #     if desc:
    #         self.fileInfo = desc
    #
    #     if bundle_identifier:
    #         self.bundle_identifier = bundle_identifier
    #
    # mobile_bundle_identifier = self.mobile_application.bundle_identifier
    #
    # logger.info("上传文件的 application id :" + self.bundle_identifier)
    # logger.info("在Mobile application中约定的 application id :" + mobile_bundle_identifier)
    # if self.bundle_identifier != mobile_bundle_identifier:
    #     raise Exception("唯一标识符跟约定的不一致，请检查后再上传")
    #
    #     super(IOSAppInfo, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Mobile Application-IOS版本'
        verbose_name_plural = 'Mobile Application-IOS版本'

    serverVersion.verbose_name = '版本号'
    versionCode.verbose_name = '唯一码'

    def __unicode__(self):
        record_id = '(id:' + str(self.id) + ')'
        record_version = '(serverVersion:' + self.serverVersion + ')'
        record_version_code = '(versionCode:' + self.versionCode + ')'
        return self.name + record_id + record_version + record_version_code


class AndroidAppInfo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    name = models.CharField(max_length=200, verbose_name='App name', default='', )
    serverVersion = models.CharField(max_length=200)
    versionCode = models.CharField(max_length=200)
    updateUrl = models.URLField(max_length=200)
    path = models.FileField(max_length=200, upload_to=install_package_file_name, validators=[validate_apk_extension])
    serviceUpdateMsg = models.TextField(max_length=400)
    # 表示android程序名
    sid = models.TextField(max_length=100, blank=True)
    createTime = models.DateTimeField(auto_now_add=True)
    isDistribution = models.BooleanField()
    size = models.CharField(max_length=200, blank=True)
    size.verbose_name = '文件大小'

    packpage_md5 = models.CharField(max_length=200, blank=True, verbose_name='文件md5码')

    mobile_application = models.ForeignKey(MobileApplication,
                                           related_name='mobile_application_android',
                                           verbose_name='所属 Mobile Application',
                                           help_text='所属 Mobile Application')

    historyDistribution = models.BooleanField(default=False)
    historyDistribution.help_text = '是否为历史发布的版本'
    historyDistribution.verbose_name = '历史版本'

    stableVersion = models.BooleanField(default=False,
                                        verbose_name='稳定版本',
                                        help_text='对应于线上版本的测试版本，便于查找历史可用的稳定版本（每次线上发版，请同步勾选一下对应的测试版本的此选项）')

    serverVersion.verbose_name = '版本号'
    versionCode.verbose_name = '唯一码'
    updateUrl.verbose_name = '升级地址'
    path.verbose_name = 'apk包地址'
    serviceUpdateMsg.verbose_name = '升级内容'

    isDistribution.help_text = '设置为发布版本后，会下线已存在的发布版本'
    isDistribution.verbose_name = '发布版本'

    isPreDistribution = models.BooleanField(default=False)
    isPreDistribution.help_text = '设置为预发布版本后，可进行灰度控制'
    isPreDistribution.verbose_name = '预发布版本'

    forceOnline = models.BooleanField(default=False)
    forceOnline.help_text = '选中后，会强制设定当前版本为最新版本（包含已升级的版本）'
    forceOnline.verbose_name = '强制上线'

    versionTimestamps = models.CharField(max_length=200, blank=True)
    versionTimestamps.help_text = '版本时间戳，用于测试版，版本控制'
    versionTimestamps.verbose_name = '版本时间戳'

    buildType = models.CharField(max_length=200, blank=True)
    buildType.help_text = '版本构建类型，SIT，UAT， DISTRIBUTION'
    buildType.verbose_name = '构建类型'

    changeLog = models.TextField(max_length=2000, blank=True)
    changeLog.help_text = 'git提交记录'
    changeLog.verbose_name = '代码改动记录'

    gitUrl = models.CharField(max_length=100, blank=True)
    gitUrl.help_text = 'git url'
    gitUrl.verbose_name = 'git url'

    gitBranch = models.CharField(max_length=100, blank=True)
    gitBranch.help_text = 'git分支'
    gitBranch.verbose_name = 'git分支'

    gitCommit = models.CharField(max_length=100, blank=True)
    gitCommit.help_text = 'git提交hashcode'
    gitCommit.verbose_name = 'git commit code'

    jira_project_key = models.CharField(max_length=100, blank=True)
    jira_project_key.help_text = '对应jira项目KEY'
    jira_project_key.verbose_name = '对应jira项目KEY'

    jira_version = models.CharField(max_length=100, blank=True)
    jira_version.help_text = '对应jira版本信息'
    jira_version.verbose_name = '对应jira版本信息'

    isSendRemoteServer = models.BooleanField(default=False)
    isSendRemoteServer.help_text = '是否发送到远程服务器'
    isSendRemoteServer.verbose_name = '发送服务器状态'

    bundle_identifier = models.CharField(
        max_length=200,
        verbose_name='Bundle identifier',
        default='',
        help_text='e.g. org.example.app'
    )
    display_image = models.ImageField(
        upload_to=normalize_image_filename,
        verbose_name='display image',
        default='',
        help_text='57x57 PNG',
        blank=True
    )
    full_size_image = models.ImageField(
        upload_to=normalize_image_filename,
        verbose_name='full size image',
        default='',
        help_text='512x512 PNG',
        blank=True
    )

    def get_display_image_url(self):
        return parse_to_url_http(self.display_image.url)

    def get_binary_url(self):
        if not self.path:
            return None

        # return remote_app_url(self.path.url, "http", self)
        return parse_to_url_http(self.path.url)

    def get_qrcode_url(self):
        if not self.path:
            return None

        return parse_to_url_http(reverse('alps:preview_app', kwargs={'app_id': str(self.uuid)}))

    # def save(self, *args, **kwargs):
    #     logger.info(self.path.file)
    #     unzipped_apk = checkapk.APK(self.path.file, raw=True)
    #     self.versionCode = unzipped_apk.get_androidversion_code()
    #     self.serverVersion = unzipped_apk.get_androidversion_name()
    #     self.bundle_identifier = unzipped_apk.get_package()
    #
    #     mobile_bundle_identifier = self.mobile_application.bundle_identifier
    #
    #     logger.info("上传文件的 application id :" + self.bundle_identifier)
    #     logger.info("在Mobile application中约定的 application id :" + mobile_bundle_identifier)
    #     if self.bundle_identifier != mobile_bundle_identifier:
    #         raise Exception("唯一标识符跟约定的不一致，请检查后再上传")
    #
    #     super(AndroidAppInfo, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Mobile Application-Android版本'
        verbose_name_plural = 'Mobile Application-Android版本'

    def __unicode__(self):
        record_id = '(id:' + str(self.id) + ')'
        record_version = '(serverVersion:' + self.serverVersion + ')'
        record_version_code = '(versionCode:' + self.versionCode + ')'
        return self.name + record_id + record_version + record_version_code

# remove android patch file
# class AndroidDiffPatchInfo(models.Model):
#     from_model = models.ForeignKey(AndroidAppInfo, related_name='from_android_app_diff_patch', verbose_name='历史包',
#                                    help_text='历史包')
#     to_model = models.ForeignKey(AndroidAppInfo, related_name='to_android_app_diff_patch', verbose_name='目标包',
#                                  help_text='目标包')
#
#     patch_path = models.FileField(max_length=200, upload_to=android_patch_file_name)
#
#     patch_md5 = models.CharField(max_length=200, verbose_name='patch包md5码', default='', )
#
#     patch_size = models.CharField(max_length=200, blank=True, verbose_name='patch文件大小')
#
#     createTime = models.DateTimeField(auto_now_add=True)
#
#     isSendRemoteServer = models.BooleanField(default=False)
#     isSendRemoteServer.help_text = '是否发送到远程服务器'
#     isSendRemoteServer.verbose_name = '发送服务器状态'
#
#     def get_path_url(self):
#         return remote_url(self.patch_path.url, "http", self, settings.BSDIFF_REMOTE_DIR)
#         # return parse_to_url_http(self.patch_path.url)
#
#     # def get_path_url(self):
#     #     if not self.path:
#     #         return None
#     #
#     #     return remote_app_url(self.patch_path.url, "http", self)
#
#     class Meta:
#         verbose_name = 'Mobile Application-Android Patch 版本'
#         verbose_name_plural = 'Mobile Application-Android Patch 版本'
#
#     def __unicode__(self):
#         record_id = '(id:' + str(self.id) + ')'
#         from_model_version = '(fromVersion:' + self.from_model.serverVersion + ')'
#         to_model_version = '(toVersion:' + self.to_model.serverVersion + ')'
#
#         return record_id + from_model_version + to_model_version


# @receiver(post_save, sender=IOSAppInfo)
# def ios_app_info_after(sender, created, instance, **kwargs):
#     if created:
#         status, output = send_app_file_to_remote_server(instance)
#         if status == 0:
#             instance.isSendRemoteServer = True
#             instance.save()
#
#
# @receiver(post_save, sender=AndroidAppInfo)
# def android_app_info_after(sender, created, instance, **kwargs):
#     logger.info("execute android_app_info_after method.")
#
#     if created:
#         status, output = send_app_file_to_remote_server(instance)
#         if status == 0:
#             instance.isSendRemoteServer = True
#             instance.save()


@receiver(post_save, sender=DownloadPageConfiguration)
def download_page_configuration_after(sender, created, instance, **kwargs):
    if created:
        logger.info("execute download_page_configuration_after")
        logger.info(instance.path.file)
        logger.info(instance.path.url)

        def get_file_dir(path):
            return os.path.dirname(path)

        full_dir = settings.FILE_HOME + get_file_dir(instance.path.url)
        full_path = settings.FILE_HOME + instance.path.url
        logger.info("full_path" + full_path)
        zfile.extract(full_path, full_dir)

        logger.info("full_dir" + full_dir)

        macosx = full_dir + "/__MACOSX"
        if os.path.exists(macosx):
            shutil.rmtree(macosx)


# @receiver(post_save, sender=AndroidDiffPatchInfo)
# def android_app_diff_patch_info_after(sender, created, instance, **kwargs):
#     logger.info("execute android_app_diff_patch_info_after method.")
#
#     if created:
#         status, output = send_patch_file_to_remote_server(instance.patch_path.url, settings.BSDIFF_REMOTE_DIR)
#         if status == 0:
#             instance.isSendRemoteServer = True
#             instance.save()


# ##########
# ##########
# ####删除逻辑######
# ##########
# ##########

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings


def filename(instance):
    return os.path.basename(instance.path.name)


def patch_filename(instance):
    return os.path.basename(instance.patch_path.name)


def package_remote_dir(instance):
    file_dir = "default"
    app_group_name = instance.mobile_application.mobile_application_group.type
    logger.info("get send file object in group:" + app_group_name)

    if len(app_group_name) > 0:
        file_dir = app_group_name

    return file_dir


@receiver(post_delete, sender=IOSAppInfo)
def delete_ios_package_files(sender, instance, **kwargs):
    full_path = settings.FILE_HOME + instance.path.url
    print full_path
    print os.path.isfile(full_path)
    if os.path.isfile(full_path):
        os.remove(full_path)

    file_name = filename(instance)
    logger.info("file name to remove: " + file_name)
    # rm_file_to_remote_server(file_name, package_remote_dir(instance))


@receiver(post_delete, sender=AndroidAppInfo)
def delete_android_package_files(sender, instance, **kwargs):
    full_path = settings.FILE_HOME + instance.path.url
    print full_path
    print os.path.isfile(full_path)
    if os.path.isfile(full_path):
        os.remove(full_path)

    file_name = filename(instance)
    logger.info("file name to remove: " + file_name)
    # rm_file_to_remote_server(file_name, package_remote_dir(instance))


# @receiver(post_delete, sender=AndroidDiffPatchInfo)
# def delete_android_diff_package_files(sender, instance, **kwargs):
#     full_path = settings.FILE_HOME + instance.patch_path.url
#     print full_path
#     print os.path.isfile(full_path)
#     if os.path.isfile(full_path):
#         os.remove(full_path)
#
#     file_name = patch_filename(instance)
#     logger.info("file name to remove: " + file_name)
#     rm_file_to_remote_server(file_name, settings.BSDIFF_REMOTE_DIR)
