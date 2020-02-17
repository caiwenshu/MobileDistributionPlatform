# -*- coding: utf-8 -*-

from django.contrib import admin

# Register your models here.
from .models import *

import checkipa
import parseapk


class MobileApplicationGroupAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {
            'fields': ['name', 'type']}),
    ]
    list_display = ('id', 'name', 'type')
    list_filter = ['name', 'type']
    search_fields = ['name', 'type']
    list_per_page = 100


admin.site.register(MobileApplicationGroup, MobileApplicationGroupAdmin)


class MobileApplicationAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {
            'fields': ['name', 'platform', 'mobile_application_group', 'bundle_identifier']}),
    ]
    list_display = ('id', 'name', 'platform', 'mobile_application_group', 'bundle_identifier', 'createTime', 'uuid')
    list_filter = ['name', 'mobile_application_group']
    search_fields = ['name', 'mobile_application_group']
    list_per_page = 100


admin.site.register(MobileApplication, MobileApplicationAdmin)


class EmailConfigurationAdmin(admin.ModelAdmin):
    fields = ('name', 'email', 'environment', 'mobile_application_group')
    list_display = ('id', 'name', 'email', 'environment', 'mobile_application_group')
    list_filter = ['email', 'environment', 'mobile_application_group']
    search_fields = ['email', 'name', 'environment', 'mobile_application_group']
    list_per_page = 100


admin.site.register(EmailConfiguration, EmailConfigurationAdmin)


class DownloadPageConfigurationAdmin(admin.ModelAdmin):
    fields = ('mobile_application_group', 'name', 'path', 'rootHtml', 'isDistribution')
    list_display = ('id', 'mobile_application_group',
                    'name',
                    'path',
                    'rootHtml',
                    'isDistribution',
                    'file_link',
                    'download_file_link')

    list_filter = ['mobile_application_group', 'name', 'isDistribution']
    search_fields = ['name']
    list_per_page = 100

    def file_link(self, obj):
        if obj.path:
            r_html = "index.html"
            if not obj.rootHtml == "":
                r_html = obj.rootHtml
            file_dir = os.path.dirname(obj.path.url)
            full_path = file_dir + "/" + r_html
            logger.info(r_html)
            return "<a href='%s' target='_'>预览</a>" % full_path
        else:
            return "No attachment"

    file_link.allow_tags = True
    file_link.short_description = '预览'

    def download_file_link(self, obj):
        if obj.path:
            return "<a href='%s' download>下载</a>" % (obj.path.url,)
        else:
            return "No attachment"

    download_file_link.allow_tags = True
    download_file_link.short_description = '下载'

    def save_model(self, request, obj, form, change):

        if obj.isDistribution:
            try:
                download_list = DownloadPageConfiguration.objects.filter(isDistribution=True,
                                                                         mobile_application_group=obj.mobile_application_group).exclude(
                    pk=obj.id)
                for info in download_list:
                    info.isDistribution = False
                    info.save()

            except DownloadPageConfiguration.DoesNotExist:
                print("DownloadPageConfiguration.DoesNotExist.")

        super(DownloadPageConfigurationAdmin, self).save_model(request, obj, form, change)


admin.site.register(DownloadPageConfiguration, DownloadPageConfigurationAdmin)


class IOSAppInfoAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {'fields': ['mobile_application',
                                         'updateUrl',
                                         'path',
                                         'serviceUpdateMsg',
                                         'versionCode',
                                         'size',
                                         'isDistribution',
                                         'isPreDistribution',
                                         'forceOnline',
                                         'stableVersion']}),
    ]
    list_display = (
    'id', 'name', 'uuid', 'bundle_identifier', 'mobile_application', 'serverVersion', 'buildType', 'image_tag',
    'updateUrl',
    'versionCode', 'size', 'isDistribution', 'isPreDistribution', 'historyDistribution',
    'stableVersion', 'createTime', 'forceOnline', 'isSendRemoteServer', 'app_preview_link',
    'app_send_email', 'path',
    'app_change_log', 'gitUrl', 'gitBranch', 'gitCommit', 'jira_version', 'jira_project_key')
    list_filter = ['serverVersion', 'isDistribution', 'mobile_application', 'isPreDistribution',
                   'historyDistribution', 'buildType', 'stableVersion']
    search_fields = ['serverVersion', 'isDistribution', 'isPreDistribution', 'buildType', 'mobile_application']
    list_per_page = 100

    def image_tag(self,  obj):
        if obj.display_image:
            full_path = obj.get_display_image_url()
            return u'<img src="%s"  style="width:50px;height:50px"/>' % full_path
        else:
            return ""

    image_tag.short_description = 'Icon'
    image_tag.allow_tags = True

    # def upload_link(self, obj):
    #     if obj.path:
    #         return "<a href='%s' target='_'>上传</a>" % (
    #         str(reverse('alps:send_remoteserver', kwargs={'app_id': str(obj.uuid)})))
    #         #  ("preview", str(obj.uuid))
    #     else:
    #         return "No attachment"

    # upload_link.allow_tags = True
    # upload_link.short_description = '上传服务器'

    def app_preview_link(self, obj):
        if obj.path:
            return "<a href='%s' target='_'>预览</a>" % (str(reverse('alps:preview_app', kwargs={'app_id':
                                                                                                   str(obj.uuid)})))
            #  ("preview", str(obj.uuid))
        else:
            return "No attachment"

    app_preview_link.allow_tags = True
    app_preview_link.short_description = '预览'

    def app_change_log(self, obj):
        logs = str(obj.changeLog).split("\n")
        print(logs)
        if len(logs) > 0:
            return logs[0]
        return obj.changeLog

    app_change_log.allow_tags = True
    app_change_log.short_description = 'git提交记录'

    def app_send_email(self, obj):
        if obj.path:
            return "<a href='%s' target='_'>发送邮件</a>" % (str(reverse('alps:send_email', kwargs={'app_id':
                                                                                                    str(obj.uuid)})))
            #  ("preview", str(obj.uuid))
        else:
            return "No attachment"

    app_send_email.allow_tags = True
    app_send_email.short_description = '发送邮件'

    def save_model(self, request, obj, form, change):

        if not change:
            _parse_ipa(obj)

        if obj.isDistribution:
            try:
                app_list = IOSAppInfo.objects.filter(isDistribution=True,
                                                     mobile_application=obj.mobile_application).exclude(pk=obj.id)
                for info in app_list:
                    info.isDistribution = False
                    info.historyDistribution = True
                    info.save()

            except IOSAppInfo.DoesNotExist:
                print("AppInfo.DoesNotExist.")

        if obj.isPreDistribution:
            try:
                app_list = IOSAppInfo.objects.filter(isPreDistribution=True,
                                                     mobile_application=obj.mobile_application).exclude(pk=obj.id)
                for info in app_list:
                    info.isPreDistribution = False
                    info.save()

            except IOSAppInfo.DoesNotExist:
                print("AppInfo.DoesNotExist.")
        super(IOSAppInfoAdmin, self).save_model(request, obj, form, change)


admin.site.register(IOSAppInfo, IOSAppInfoAdmin)


class AndroidAppInfoAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {'fields': ['mobile_application', 'updateUrl', 'path', 'serviceUpdateMsg',
                                         'size', 'isDistribution', 'isPreDistribution',
                                         'forceOnline', 'stableVersion']}),
    ]
    # inlines = [ChoiceInline]
    list_display = (
    'id', 'name', 'uuid', 'bundle_identifier', 'mobile_application', 'serverVersion', 'buildType', 'image_tag',
    'versionCode', 'updateUrl', 'size', 'isDistribution', 'isPreDistribution', 'historyDistribution',
    'stableVersion', 'createTime', 'forceOnline', 'isSendRemoteServer', 'app_preview_link',
    'app_send_email',
    'path', 'app_change_log', 'gitUrl', 'gitBranch', 'gitCommit', 'jira_version', 'jira_project_key', 'packpage_md5')
    list_filter = ['serverVersion', 'isDistribution', 'mobile_application', 'isPreDistribution', 'historyDistribution',
                   'buildType', 'stableVersion']
    search_fields = ['serverVersion', 'isDistribution', 'mobile_application', 'isPreDistribution', 'buildType']
    list_per_page = 100

    def image_tag(self, obj):
        if obj.display_image:
            full_path = obj.get_display_image_url()
            return u'<img src="%s"  style="width:50px;height:50px"/>' % full_path
        else:
            return ""

    image_tag.short_description = 'Icon'
    image_tag.allow_tags = True

    # def upload_link(self, obj):
    #     if obj.path:
    #         return "<a href='%s' target='_'>上传</a>" % (str(reverse(
    #             'alps:send_remoteserver', kwargs={'app_id': str(obj.uuid)})))
    #         #  ("preview", str(obj.uuid))
    #     else:
    #         return "No attachment"
    #
    # upload_link.allow_tags = True
    # upload_link.short_description = '上传服务器'

    def app_preview_link(self, obj):
        if obj.path:
            return "<a href='%s' target='_'>预览</a>" % (str(reverse(
                'alps:preview_app', kwargs={'app_id': str(obj.uuid)})))
            #  ("preview", str(obj.uuid))
        else:
            return "No attachment"

    app_preview_link.allow_tags = True
    app_preview_link.short_description = '预览'

    def app_change_log(self, obj):
        logs = str(obj.changeLog).split("\n")
        print(logs)
        if len(logs) > 0:
            return logs[0]
        return obj.changeLog

    app_change_log.allow_tags = True
    app_change_log.short_description = 'git提交记录'

    def app_send_email(self, obj):
        if obj.path:
            return "<a href='%s' target='_'>发送邮件</a>" % (str(reverse('alps:send_email', kwargs={'app_id':
                                                                                                    str(obj.uuid)})))
            #  ("preview", str(obj.uuid))
        else:
            return "No attachment"

    app_send_email.allow_tags = True
    app_send_email.short_description = '发送邮件'

    def save_model(self, request, obj, form, change):

        logger.info(obj)
        logger.info(change)

        if not change:
            _parse_apk(obj)

        if obj.isDistribution:
            try:
                app_list = AndroidAppInfo.objects.filter(isDistribution=True,
                                                         mobile_application=obj.mobile_application).exclude(pk=obj.id)
                for info in app_list:
                    info.isDistribution = False
                    info.historyDistribution = True
                    info.save()

            except AndroidAppInfo.DoesNotExist:
                print("AndroidAppInfoAdmin.DoesNotExist.")

        if obj.isPreDistribution:
            try:
                app_list = AndroidAppInfo.objects.filter(isPreDistribution=True,
                                                         mobile_application=obj.mobile_application).exclude(pk=obj.id)
                for info in app_list:
                    info.isPreDistribution = False
                    info.save()

            except AndroidAppInfo.DoesNotExist:
                print("AndroidAppInfo.DoesNotExist.")

        super(AndroidAppInfoAdmin, self).save_model(request, obj, form, change)


admin.site.register(AndroidAppInfo, AndroidAppInfoAdmin)


# class AndroidDiffPatchInfoAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ('Date information', {'fields': ['from_model', 'to_model', 'patch_path', 'patch_md5',
#                                          'patch_size']}),
#     ]
#     # inlines = [ChoiceInline]
#     list_display = (
#     'id', 'from_model', 'to_model', 'patch_path', 'patch_md5', 'patch_size', 'createTime', 'isSendRemoteServer')
#     list_filter = ['from_model', 'to_model']
#     search_fields = ['id']
#     list_per_page = 100
#
#     # def upload_link(self, obj):
#     #     if obj.path:
#     #         return "<a href='%s' target='_'>上传</a>" % (str(reverse(
#     #             'alps:send_remoteserver', kwargs={'app_id': str(obj.uuid)})))
#     #         #  ("preview", str(obj.uuid))
#     #     else:
#     #         return "No attachment"
#     # upload_link.allow_tags = True
#     # upload_link.short_description = '上传服务器'
#
#
# admin.site.register(AndroidDiffPatchInfo, AndroidDiffPatchInfoAdmin)


def _parse_ipa(app_info):
    if settings.IOS != app_info.mobile_application.platform:
        raise Exception('upload file and selected mobile application platform conflict.')

    logger.info("upload success IOS file with name %s", app_info.path.name)

    # parse ipa file and read content
    parse = checkipa.ParseIPA(app_info.path)
    params = {'parse': parse, 'ipa_filename': app_info.path.name,
              'check_udids': False, 'udids': None,
              'verbose': False}
    return_info = checkipa.process_ipa(params)
    file_info = return_info['desc']
    bundle_identifier = return_info['bundle_identifier']
    bundle_name = return_info['bundle_name']
    version = return_info['version']

    logger.info(return_info)

    mobile_bundle_identifier = app_info.mobile_application.bundle_identifier

    logger.info("上传文件的 application id :" + bundle_identifier)
    logger.info("在Mobile application中约定的 application id :" + mobile_bundle_identifier)
    if bundle_identifier != mobile_bundle_identifier:
        raise Exception("唯一标识符跟约定的不一致，请检查后再上传")

    app_info.name = bundle_name
    app_info.bundle_identifier = bundle_identifier
    app_info.file_info = file_info
    app_info.serverVersion = version

    app_info.save()


def _parse_apk(app_info):
    if settings.ANDROID != app_info.mobile_application.platform:
        raise Exception('upload file and selected mobile application platform conflict.')

    logger.info("upload success Android file with name %s", app_info.path.name)
    logger.info(app_info.path.url)
    logger.info(app_info.path.file)
    logger.info(app_info.path.file.temporary_file_path())

    logger.info("begin parse apk file")
    status, bundle_identifier, version_code, version_mame, app_name, icon_path, unzip_dir = parseapk.parse(
        app_info.path.file.temporary_file_path())

    logger.info("end parse apk file")
    logger.info("status:" + str(status))
    logger.info("bundle_identifier:" + bundle_identifier)
    logger.info("version_code:" + version_code)
    logger.info("version_mame:" + version_mame)
    logger.info("app_name:" + app_name)

    if status != 0:
        raise Exception('apk file parse fail. please check apk file')

    from django.core.files import File

    file_object = open(icon_path, "rb")
    django_file = File(file_object)
    logger.info("django_file:")
    logger.info(django_file)

    mobile_bundle_identifier = app_info.mobile_application.bundle_identifier

    logger.info("上传文件的 application id :" + bundle_identifier)
    logger.info("在Mobile application中约定的 application id :" + mobile_bundle_identifier)
    if bundle_identifier != mobile_bundle_identifier:
        raise Exception("唯一标识符跟约定的不一致，请检查后再上传")

    app_info.name = app_name
    app_info.bundle_identifier = bundle_identifier
    app_info.versionCode = version_code
    app_info.serverVersion = version_mame
    app_info.display_image = django_file

    app_info.save()
