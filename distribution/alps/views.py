# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render

from django.http import StreamingHttpResponse

from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.exceptions import APIException

from .models import *
import filesize
from .sendemail import send_template_mail
import checkipa
import parseapk

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponse, Http404, HttpResponseRedirect
from utils import parse_to_url_http

import qrcode
from cStringIO import StringIO

from django.utils import timezone

try:
    from django.contrib.sites.models import get_current_site
except ImportError:
    from django.contrib.sites.shortcuts import get_current_site


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


# Create your views here.
class UploadFileApiView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    parser_classes = (MultiPartParser, FormParser,)
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):

        return Response(status=204)

    def post(self, request, format=None):

        is_distribution = False
        service_update_msg = ""
        update_url = None
        build_type = ""
        change_log = ""
        git_url = ""
        git_branch = ""
        git_commit = ""
        jira_project_key = ""
        jira_version = ""

        if not 'file' in request.data:
            raise APIException('request.data missing key "file"')

        if 'serviceUpdateMsg' in request.data:
            service_update_msg = request.data['serviceUpdateMsg']

        if 'isDistribution' in request.data:
            is_distribution = (request.data['isDistribution'] == "1")

        if 'updateUrl' in request.data:
            update_url = request.data['updateUrl']

        if 'buildType' in request.data:
            build_type = request.data['buildType']

        # log information
        if 'changeLog' in request.data:
            change_log = request.data['changeLog']

        if 'gitUrl' in request.data:
            git_url = request.data['gitUrl']

        if 'gitBranch' in request.data:
            git_branch = request.data['gitBranch']

        if 'gitCommit' in request.data:
            git_commit = request.data['gitCommit']

        if 'jira_project_key' in request.data:
            jira_project_key = request.data['jira_project_key']

        if 'jira_version' in request.data:
            jira_version = request.data['jira_version']

        file_obj = request.data['file']

        file_type = file_obj.name.split('.')[-1]

        platform = settings.IOS

        if file_type.lower() == "apk":
            platform = settings.ANDROID

            app_info = _parse_and_save_apk(file_obj, service_update_msg, is_distribution, update_url,
                                           build_type, change_log, git_url, git_branch, git_commit, jira_project_key,
                                           jira_version)

            # if 'android_lint_report' in request.data:
            #     android_lint_report = request.data['android_lint_report']
            #     _parse_android_lint_report(android_lint_report, app_info.mobile_application, app_info)

            # 获取最近5个版本,并生成差量包
            # filter(mobile_application_group=mobile_application_group)
            # _generate_package_diff(app_info)
            # tasks.task_package_diff.delay(app_info.id)

        if file_type.lower() == "ipa":
            app_info = _parse_and_save_ipa(file_obj, service_update_msg, is_distribution, update_url,
                                           build_type, change_log, git_url, git_branch, git_commit, jira_project_key,
                                           jira_version)

        app_url = reverse('alps:generate_qrcode', kwargs={'app_id': str(app_info.uuid)})
        base_url = parse_to_url_http(app_url)
        logger.info("generate QR code url :" + base_url)

        from django.db.models import Q

        mobile_application_group = app_info.mobile_application.mobile_application_group
        email_conf = EmailConfiguration.objects.filter((Q(environment__contains=build_type) |
                                                        Q(environment__contains="all")) &
                                                       Q(mobile_application_group=mobile_application_group))

        email_name = []

        for emailEnt in email_conf:
            email_name.append(emailEnt.email)

        send_template_mail(base_url, app_info, platform, email_name)

        return JSONResponse(data={
            'code': '200',
            'data': {'name': app_info.name,
                     'server_version': app_info.serverVersion,
                     'update_url': app_info.updateUrl,
                     'size': app_info.size,
                     'uuid': app_info.uuid,
                     'bundle_identifier': app_info.bundle_identifier,
                     'display_image_url': app_info.get_display_image_url(),
                     'qr_url': app_info.get_qrcode_url()},
            'message': 'success'
        })
        # return Response(status=200)


def send_email(request, app_id):
    platform = settings.IOS
    try:
        app_info = IOSAppInfo.objects.get(uuid=app_id)
    except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):
        platform = settings.ANDROID
        app_info = get_object_or_404(AndroidAppInfo, uuid=app_id)

    app_url = reverse('alps:generate_qrcode', kwargs={'app_id': str(app_info.uuid)})
    base_url = parse_to_url_http(app_url)
    logger.info("generate QR code url :" + base_url)

    logger.info("******")
    logger.info(app_info.changeLog)
    logger.info("******")

    from django.db.models import Q

    mobile_application_group = app_info.mobile_application.mobile_application_group
    email_conf = EmailConfiguration.objects.filter(Q(environment__contains="all") &
                                                   Q(mobile_application_group=mobile_application_group))

    email_name = []

    for emailEnt in email_conf:
        email_name.append(emailEnt.email)

    send_template_mail(base_url, app_info, platform, email_name)

    return JSONResponse({'status': '200', 'output': '邮件发送成功！请检查邮箱'})


def preview_app(request, app_id):
    platform = settings.IOS
    try:
        app_info = IOSAppInfo.objects.get(uuid=app_id)
    except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):
        app_info = get_object_or_404(AndroidAppInfo, uuid=app_id)
        platform = settings.ANDROID

    return render(request, 'alps/app_list.html', {
        'appInfo': app_info,
        'platform': platform,
        'ios_identifier': settings.IOS,
        'site_url': get_current_site(request).domain,
    })


# def send_remoteserver(request, app_id):
#     app_info = None
#     platform = settings.IOS
#     try:
#         app_info = IOSAppInfo.objects.get(uuid=app_id)
#     except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):
#         app_info = get_object_or_404(AndroidAppInfo, uuid=app_id)
#         platform = settings.ANDROID
#
#     print(platform)
#     status, output = send_app_file_to_remote_server(app_info)
#
#     if status == 0:
#         app_info.isSendRemoteServer = True
#         app_info.save()
#
#     return JSONResponse({'status': status, 'output': output})


def send_apk(request, app_id):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    android_app = None
    try:
        android_app = AndroidAppInfo.objects.get(uuid=app_id)
    except (AndroidAppInfo.DoesNotExist, MultipleObjectsReturned):
        return HttpResponse('App does not exist', status=404)

    def get_filename(path):
        return os.path.basename(path)

    the_file_name = get_filename(android_app.path.url)

    fullPath = settings.FILE_HOME + android_app.path.url
    print(fullPath)

    def file_iterator(file_name, chunk_size=512):
        with open(file_name, 'r') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    # the_file_name = "big_file.pdf"
    response = StreamingHttpResponse(file_iterator(fullPath))
    # response = HttpResponse(FileWrapper(open(filename, 'rb')))
    response['Content-Length'] = os.path.getsize(fullPath)
    response['Content-Type'] = settings.MOBILE_APP_DISTRIBUTION_CONTENT_TYPES[settings.ANDROID]
    response['Content-Disposition'] = 'inline; filename=%s' % the_file_name
    return response


# def download_distribution(request):
#
#     user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
#     logger.info(user_agent)
#
#     app_info = None
#     platform = settings.IOS
#
#     status = request.GET.get("status", None)
#
#     if "android" in user_agent:
#         logger.info("android")
#         if status == "pre":
#
#             app_info = get_object_or_404(AndroidAppInfo, isPreDistribution=True)
#         else:
#             app_info = get_object_or_404(AndroidAppInfo, isDistribution=True)
#
#         platform = settings.ANDROID
#
#     if "ios" in user_agent or "ipad" in user_agent or "mac" in user_agent or "iphone" in user_agent:
#         logger.info("ios")
#
#         if status == "pre":
#             app_info = get_object_or_404(IOSAppInfo, isPreDistribution=True)
#         else:
#             app_info = get_object_or_404(IOSAppInfo, isDistribution=True)
#
#     return render(request, 'alps/download.html', {
#         'appInfo': app_info,
#         'platform': platform,
#         'ios_identifier': settings.IOS,
#     })


def application_information(request, tp):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    logger.info(user_agent)
    logger.info("************************************")

    try:
        mobile_application_group = MobileApplicationGroup.objects.get(type=tp)
    except (MobileApplicationGroup.DoesNotExist, MultipleObjectsReturned):
        raise APIException('系统出错啦，请确认 type 是否正确')

    app_info = None
    platform = settings.IOS

    status = request.GET.get("status", None)
    logger.info(status)

    d_url = ""

    if "ios" in user_agent or "ipad" in user_agent or "mac" in user_agent or "iphone" in user_agent:
        logger.info("ios")
        logger.info(mobile_application_group)

        try:
            if status == "pre":

                app_info = _get_ios_pre_distribution_version(group=mobile_application_group)

            else:

                app_info = _get_ios_normal_distribution_version(group=mobile_application_group)

        except IOSAppInfo.DoesNotExist:
            raise APIException("找不到对应的发布包，请联系管理员")

        logger.info(app_info)

        d_url = "itms-services://?action=download-manifest&url=%s" % app_info.get_plist_url()

    else:
        logger.info("android")

        try:
            if status == "pre":
                app_info = _get_android_pre_distribution_version(group=mobile_application_group)
            else:
                app_info = _get_android_normal_distribution_version(group=mobile_application_group)

        except AndroidAppInfo.DoesNotExist:
            raise APIException("找不到对应的安卓下载包，请联系管理员")

        d_url = app_info.get_binary_url()
        platform = settings.ANDROID

    # logger.info("*****")
    # str_time = app_info.createTime.strftime('%Y-%m-%d %H:%M')
    # format_date = datetime.datetime.strptime(str_time, '%Y-%m-%d %H:%M')
    # logger.info(format_date)
    # logger.info("*****")
    logger.info(timezone.localtime(app_info.createTime).strftime('%Y-%m-%d %H:%M'))
    logger.info(timezone.get_current_timezone())
    logger.info(app_info.createTime)
    format_time = timezone.localtime(app_info.createTime).strftime('%Y-%m-%d %H:%M')

    return_json = {'version': app_info.serverVersion,
                   'size': app_info.size,
                   'time': format_time,
                   'url': d_url,
                   'platform': platform,
                   'ios_identifier': settings.IOS,
                   'distribution_url': parse_to_url_http("/alps/download/%s" % tp)}
    logger.info(return_json)

    response_json = JSONResponse(return_json)
    response_json.__setitem__("Access-Control-Allow-Origin", "*")
    return response_json


def dynamic_download_distribution(request, type):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    logger.info(user_agent)

    query_string = request.META.get('QUERY_STRING', '')
    logger.info(query_string)

    try:
        mobile_application_group = MobileApplicationGroup.objects.get(type=type)
    except (MobileApplicationGroup.DoesNotExist, MultipleObjectsReturned):
        raise APIException('系统出错啦，请确认地址是否正确')

    try:
        page = DownloadPageConfiguration.objects.get(mobile_application_group=mobile_application_group,
                                                     isDistribution=True)
    except (DownloadPageConfiguration.DoesNotExist, MultipleObjectsReturned):
        raise APIException('找不到下载页面，请联系管理人员')

    if len(query_string) > 0:
        query_string = "?" + query_string
    r_html = page.rootHtml + query_string
    file_dir = os.path.dirname(page.path.url)
    full_path = file_dir + "/" + r_html
    logger.info("download page path :" + full_path)

    # fsock = open(full_path, "r")
    #
    # lines = fsock.readlines()

    return HttpResponseRedirect(full_path)
    # return HttpResponse(lines, content_type='text/html; charset=utf-8')

    # return render_to_response(lines)
    #
    # return render(request, 'alps/download.html', {
    #     'appInfo': app_info,
    #     'platform': platform,
    #     'ios_identifier': settings.IOS,
    # })


def ios_app_plist(request, app_id):
    # app_id = "7ad64e5656024ccfb5ad6d01689f4911"
    logger.info(app_id)

    ios_app = None

    # ios_app = get_object_or_404(IOSAppInfo,uuid=app_id)
    # if ios_app :
    #     androidAppInfo = get_object_or_404(AndroidAppInfo,uuid = android_info_id)
    # else:
    #     raise Http404
    try:
        ios_app = IOSAppInfo.objects.get(uuid=app_id)
    except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):
        raise Http404

    from django.conf import settings as mad_settings

    plist = mad_settings.IOS_PLIST_BLUEPRINT

    plist = plist.replace(mad_settings.PLIST_APP_URL, ios_app.get_binary_url())
    plist = plist.replace(mad_settings.PLIST_BUNDLE_IDENTIFIER, ios_app.bundle_identifier)
    plist = plist.replace(mad_settings.PLIST_BUNDLE_VERSION, ios_app.serverVersion)
    plist = plist.replace(mad_settings.PLIST_APP_TITLE, ios_app.name)

    logger.info(plist)
    return HttpResponse(
        plist,
        content_type=mad_settings.MOBILE_APP_DISTRIBUTION_CONTENT_TYPES[mad_settings.IOS_PLIST]
    )


def generate_qrcode(request, app_id):
    logger.info("**************")
    logger.info(app_id)
    base_url = parse_to_url_http(str(reverse('alps:preview_app', kwargs={'app_id': app_id})))

    img = qrcode.make(base_url)

    buf = StringIO()
    img.save(buf)
    image_stream = buf.getvalue()

    response = HttpResponse(image_stream, content_type="image/png")
    response['Last-Modified'] = 'Mon, 27 Apr 2015 02:05:03 GMT'
    response['Cache-Control'] = 'max-age=31536000'

    return response


# 定义私有方法
def _update_to_single_distribution_ios(obj):
    if obj.isDistribution:
        try:
            app_info = IOSAppInfo.objects.filter(isDistribution=True,
                                                 mobile_application=obj.mobile_application).exclude(pk=obj.id)
            for info in app_info:
                info.isDistribution = False
                info.historyDistribution = True
                info.save()

        except IOSAppInfo.DoesNotExist:
            print("AppInfo.DoesNotExist.")


def _update_to_single_distribution_android(obj):
    if obj.isDistribution:
        try:
            app_info = AndroidAppInfo.objects.filter(isDistribution=True,
                                                     mobile_application=obj.mobile_application).exclude(pk=obj.id)
            for info in app_info:
                info.isDistribution = False
                info.historyDistribution = True
                info.save()

        except AndroidAppInfo.DoesNotExist:
            print("AndroidAppInfoAdmin.DoesNotExist.")


import zipfile
import zfile
import json
# from .models_quality import *
from django.core.files import File

# def _parse_android_lint_report(file_obj, mobile_application, android_app_info):
#     logger.info("android lint file with name %s", file_obj.name)
#     f = file_obj.temporary_file_path()
#     dir_name = os.path.dirname(f)
#     base_name = os.path.basename(f)
#     base = base_name.split('.')[0]
#     unzip_dir = dir_name + "/" + base
#     logger.info("unzip android lint file path: %s" % unzip_dir)
#
#     zfile.extract(file_obj.temporary_file_path(), unzip_dir)
#
#     content = unzip_dir + "/content.json"
#     with open(content, 'r') as load_f:
#         load_array = json.load(load_f)
#
#     summary_ignore = 0
#     summary_information = 0
#     summary_fatal = 0
#     summary_warning = 0
#     summary_error = 0
#     for lint in load_array:
#         logger.info(lint)
#         lint_xml = unzip_dir + "/" + lint["lint_xml"]
#         lint_html = unzip_dir + "/" + lint["lint_html"]
#         logger.info("lint_xml path: %s" % lint_xml)
#         logger.info("lint_html path: %s" % lint_html)
#
#         lint_xml_object = open(lint_xml, "rb")
#         lint_xml_file = File(lint_xml_object)
#         lint_html_object = open(lint_html, "rb")
#         lint_html_file = File(lint_html_object)
#
#         summary_ignore += int(lint["Ignore"])
#         summary_information += int(lint["Information"])
#         summary_fatal += int(lint["Fatal"])
#         summary_warning += int(lint["Warning"])
#         summary_error += int(lint["Error"])
#
#         app_info = AndroidLintQuality(mobile_application=mobile_application,
#                                       android_app_info=android_app_info,
#                                       module_name=lint["module_name"],
#                                       module_lint_html_report=lint_html_file,
#                                       module_lint_xml_report=lint_xml_file,
#                                       module_lint_severity_ignore=lint["Ignore"],
#                                       module_lint_severity_information=lint["Information"],
#                                       module_lint_severity_fatal=lint["Fatal"],
#                                       module_lint_severity_warning=lint["Warning"],
#                                       module_lint_severity_error=lint["Error"])
#         app_info.save()
#
#     app_info_summary = AndroidLintQualitySummary(mobile_application=mobile_application,
#                                                  android_app_info=android_app_info,
#                                                  module_lint_severity_ignore=str(summary_ignore),
#                                                  module_lint_severity_information=str(summary_information),
#                                                  module_lint_severity_fatal=str(summary_fatal),
#                                                  module_lint_severity_warning=str(summary_warning),
#                                                  module_lint_severity_error=str(summary_error))
#     app_info_summary.save()


def _parse_and_save_ipa(file_obj, service_update_msg, is_distribution, update_url,
                        build_type, change_log, git_url, git_branch, git_commit, jira_project_key, jira_version):
    logger.info("upload success IOS file with name %s", file_obj.name)

    # parse ipa file and read content
    parse = checkipa.ParseIPA(file_obj)
    params = {'parse': parse, 'ipa_filename': file_obj.name,
              'check_udids': False, 'udids': None,
              'verbose': False}
    return_info = checkipa.process_ipa(params)
    file_info = return_info['desc']
    bundle_identifier = return_info['bundle_identifier']
    bundle_name = return_info['bundle_name']
    version = return_info['version']
    full_icon_file = return_info['full_icon_file']

    django_file = None
    if len(full_icon_file) > 0:

        # read icon
        # file_object = open(full_icon_path)
        logger.info(full_icon_file)

        p, n = os.path.split(full_icon_file)
        logger.info("file path: %s, file name: %s" % (p, n))
        ext = n.split('.')
        n_new = ext[0] + "-new." + ext[1]
        output_path = os.path.join(p, n_new)
        logger.info("uncompress file path : %s" % output_path)

        from django.core.files import File

        import commands
        import pngdefry

        try:
            pngdefry.decode(full_icon_file, output_path)
        except Exception as e:
            print e
            logger.info(e)
        # comm = "java -jar %s %s" % (settings.PNG_CONVERTER_PATH, full_icon_file)

        # logger.info("convert icon commonds is :" + comm)
        #
        # status, output = commands.getstatusoutput(comm)
        #
        # logger.info(status)
        # logger.info("output:" + output)

        if os.path.isfile(output_path):
            full_icon_file = output_path

        try:

            file_object = open(full_icon_file, "rb")
            django_file = File(file_object)
            logger.info("django_file:")
            logger.info(django_file)

        except Exception as e:
            print e
            django_file = None

    # clear temp file
    # parse.clear_icon_temp_file()

    # check bundle identifier is exist in mobile application
    mobile_applications = MobileApplication.objects.filter(bundle_identifier=bundle_identifier,
                                                           platform=settings.IOS)
    if len(mobile_applications) > 1:
        raise APIException('bundle Identifier (%s) is repeat '
                           'in Mobile Application on platform by IOS. ' % bundle_identifier)

    if len(mobile_applications) > 0:
        mobile_application = mobile_applications[0]
    else:
        raise APIException('bundle Identifier (%s) is not exist '
                           'in Mobile Application on platform by IOS. ' % bundle_identifier)

    logger.info(return_info)

    app_info = IOSAppInfo(name=bundle_name,
                          path=file_obj,
                          serviceUpdateMsg=service_update_msg,
                          isDistribution=is_distribution,
                          size=filesize.size(file_obj.size),
                          buildType=build_type,
                          changeLog=change_log,
                          gitUrl=git_url,
                          gitBranch=git_branch,
                          gitCommit=git_commit,
                          serverVersion=version,  # parse from file
                          fileInfo=file_info,
                          bundle_identifier=bundle_identifier,
                          mobile_application=mobile_application,
                          display_image=django_file,
                          jira_project_key=jira_project_key,
                          jira_version=jira_version
                          )
    app_info.save()

    # full_path = settings.FILE_HOME + app_info.display_image.url
    # logger.info("full image path :" + full_path)
    # result = ipin.convent_png_to_normalize(full_path)
    # logger.info(result)

    _update_to_single_distribution_ios(app_info)

    if update_url:
        app_info.updateUrl = update_url
        app_info.save()
    else:
        app_info.updateUrl = app_info.get_qrcode_url()
        app_info.save()

    return app_info


def _parse_and_save_apk(file_obj, service_update_msg, is_distribution, update_url,
                        build_type, change_log, git_url, git_branch, git_commit, jira_project_key, jira_version):
    logger.info("upload success Android file with name %s", file_obj.name)
    logger.info(file_obj.file)
    logger.info(file_obj.temporary_file_path())

    # parse apk file and read content
    # unzipped_apk = checkapk.APK(file_obj, raw=True)
    # version_code = unzipped_apk.get_androidversion_code()
    # server_version = unzipped_apk.get_androidversion_name()
    # bundle_identifier = unzipped_apk.get_package()
    #
    # logger.info("version code:" + unzipped_apk.get_androidversion_code())
    # logger.info("version name:" + unzipped_apk.get_androidversion_name())
    # logger.info("bundle identifier:" + unzipped_apk.get_package())

    # full_path = settings.FILE_HOME + instance.path.url
    # logger.info("apk file path: " + full_path)
    logger.info("begin parse apk file")
    status, bundle_identifier, version_code, version_mame, app_name, icon_path, unzip_dir = parseapk.parse(
        file_obj.temporary_file_path())
    logger.info("end parse apk file")
    logger.info("status:" + str(status))
    logger.info("bundle_identifier:" + bundle_identifier)
    logger.info("version_code:" + version_code)
    logger.info("version_mame:" + version_mame)
    logger.info("app_name:" + app_name)

    if status != 0:
        raise APIException('apk file parse fail. please check apk file')

    from django.core.files import File

    try:

        file_object = open(icon_path, "rb")
        django_file = File(file_object)
        logger.info("django_file:")
        logger.info(django_file)

    except Exception as e:
        print e
        django_file = None

    file_md5 = md5(file_obj.temporary_file_path())

    # check bundle identifier is exist in mobile application
    mobile_applications = MobileApplication.objects.filter(bundle_identifier=bundle_identifier,
                                                           platform=settings.ANDROID)
    if len(mobile_applications) > 1:
        raise APIException('bundle Identifier (%s) is repeat '
                           'in Mobile Application on platform by Android. ' % bundle_identifier)

    if len(mobile_applications) > 0:
        mobile_application = mobile_applications[0]
    else:
        raise APIException('bundle Identifier (%s) is not exist '
                           'in Mobile Application on platform by Android. ' % bundle_identifier)

    app_info = AndroidAppInfo(name=app_name,
                              path=file_obj,
                              serviceUpdateMsg=service_update_msg,
                              isDistribution=is_distribution,
                              size=filesize.size(file_obj.size),
                              buildType=build_type,
                              changeLog=change_log,
                              gitUrl=git_url,
                              gitBranch=git_branch,
                              gitCommit=git_commit,
                              serverVersion=version_mame,  # parse from file
                              versionCode=version_code,
                              bundle_identifier=bundle_identifier,
                              mobile_application=mobile_application,
                              jira_project_key=jira_project_key,
                              jira_version=jira_version,
                              display_image=django_file,
                              packpage_md5=file_md5
                              )
    app_info.save()

    _update_to_single_distribution_android(app_info)

    if update_url:
        app_info.updateUrl = update_url
        app_info.save()
    else:
        app_info.updateUrl = app_info.get_qrcode_url()
        app_info.save()

    return app_info


def _get_ios_pre_distribution_version(group):
    try:
        app_info = IOSAppInfo.objects.get(isPreDistribution=True,
                                          mobile_application__mobile_application_group=group)

    except IOSAppInfo.DoesNotExist:
        # 找不到灰度版本，走正常版本
        app_info = _get_ios_normal_distribution_version(group)

    return app_info


def _get_ios_normal_distribution_version(group):
    app_info = IOSAppInfo.objects.get(isDistribution=True,
                                      mobile_application__mobile_application_group=group)

    return app_info


def _get_android_pre_distribution_version(group):
    try:
        app_info = AndroidAppInfo.objects.get(isPreDistribution=True,
                                              mobile_application__mobile_application_group=group)

    except AndroidAppInfo.DoesNotExist:
        # 找不到灰度版本，走正常版本
        app_info = _get_android_normal_distribution_version(group)

    return app_info


def _get_android_normal_distribution_version(group):
    app_info = AndroidAppInfo.objects.get(isDistribution=True,
                                          mobile_application__mobile_application_group=group)

    return app_info


import commands
import tempfile
import datetime

#
# def _generate_package_diff(app_info):
#     # ./bsdiff old.apk new.apk old-to-new.patch
#
#     logger.info("begin execute ... android ipa diff")
#
#     logger.info("newest apk id : id " + str(app_info.id) +
#                 " versionCode: " + app_info.versionCode +
#                 " serverVersion:" + app_info.serverVersion +
#                 " package md5: " + app_info.packpage_md5)
#
#     lastest_applist = AndroidAppInfo.objects.filter(mobile_application=app_info.mobile_application,
#                                                     historyDistribution=True).exclude(
#         pk=app_info.id).order_by('-id')[0: 5]
#
#     logger.info("get lastest histroy distribution :" + str(len(lastest_applist)))
#
#     new_package_full_path = settings.FILE_HOME + app_info.path.url
#
#     time_format = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
#
#     temp_patch_path = tempfile.mkdtemp() + time_format + ".patch"
#     logger.info(temp_patch_path)
#
#     for histroy in lastest_applist:
#
#         logger.info("current  histroy apk : id " + str(histroy.id) +
#                     " versionCode: " + histroy.versionCode +
#                     " serverVersion:" + histroy.serverVersion +
#                     " package md5: " + histroy.packpage_md5)
#
#         if histroy.packpage_md5:
#
#             diff_patchs = AndroidDiffPatchInfo.objects.filter(from_model=histroy, to_model=app_info)
#             if len(diff_patchs) > 0:
#                 logger.info("current  histroy apk is exist diff patch.")
#                 continue
#
#             logger.info("execute diff package......")
#             histroy_package_full_path = settings.FILE_HOME + histroy.path.url
#
#             logger.info(settings.BSDIFF_PATH)
#             logger.info(histroy_package_full_path)
#             logger.info(new_package_full_path)
#             logger.info(temp_patch_path)
#
#             patch_begin_time = datetime.datetime.now()
#             # long running
#
#             comm = "%s %s %s %s" % (
#             settings.BSDIFF_PATH, histroy_package_full_path, new_package_full_path, temp_patch_path)
#
#             logger.info("send file to remote server  is :" + comm)
#
#             status, output = commands.getstatusoutput(comm)
#
#             logger.info(status)
#             logger.info(output)
#
#             patch_end_time = datetime.datetime.now()
#             seconds = (patch_end_time - patch_begin_time).seconds
#             logger.info("-------path time for seconds ------: " + str(seconds) + "s")
#
#             if status == 0:
#                 from django.core.files import File
#
#                 file_object = open(temp_patch_path, "rb")
#                 django_file = File(file_object)
#                 logger.info("django_file:")
#                 logger.info(django_file)
#
#                 patch_md5 = md5(temp_patch_path)
#                 patch_size = filesize.size(django_file.size)
#
#                 diff_patch_info = AndroidDiffPatchInfo(from_model=histroy, to_model=app_info, patch_path=django_file,
#                                                        patch_md5=patch_md5, patch_size=patch_size)
#
#                 diff_patch_info.save()


# Create your views here.
class UpdateAppDistrubutionApiView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    parser_classes = (MultiPartParser, FormParser,)
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):

        return Response(status=204)

    def post(self, request, format=None):

        uuid = ""
        update_msg = ""

        if 'uuid' in request.data:
            uuid = request.data['uuid']

        if 'update_msg' in request.data:
            update_msg = request.data['update_msg']

        platform = settings.IOS

        try:
            app_info = IOSAppInfo.objects.get(uuid=uuid)
            app_info.isDistribution = True

            distribution_url = parse_to_url_http(
                "/alps/download/%s/" % app_info.mobile_application.mobile_application_group.type)
            app_info.updateUrl = distribution_url

            app_info.serviceUpdateMsg = update_msg
            app_info.save()

            _update_to_single_distribution_ios(app_info)

        except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):

            app_info = get_object_or_404(AndroidAppInfo, uuid=uuid)
            app_info.isDistribution = True
            app_info.serviceUpdateMsg = update_msg

            distribution_url = parse_to_url_http(
                "/alps/download/%s/" % app_info.mobile_application.mobile_application_group.type)
            app_info.updateUrl = distribution_url

            app_info.save()
            _update_to_single_distribution_android(app_info)
            platform = settings.ANDROID

        return JSONResponse(data={
            'code': '200',
            'data': {'name': app_info.name,
                     'server_version': app_info.serverVersion,
                     'update_url': app_info.updateUrl,
                     'size': app_info.size,
                     'uuid': app_info.uuid,
                     'bundle_identifier': app_info.bundle_identifier,
                     'display_image_url': app_info.get_display_image_url(),
                     'qr_url': app_info.get_qrcode_url()},
            'message': 'success'
        })


# Create your views here.
class GetAppDistributionApiView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    parser_classes = (MultiPartParser, FormParser,)
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):

        return Response(status=204)

    def post(self, request, format=None):

        uuid = ""

        if 'uuid' in request.data:
            uuid = request.data['uuid']

        platform = settings.IOS

        try:
            app_info = IOSAppInfo.objects.get(uuid=uuid)

        except (IOSAppInfo.DoesNotExist, MultipleObjectsReturned):

            app_info = get_object_or_404(AndroidAppInfo, uuid=uuid)

            platform = settings.ANDROID

        return JSONResponse(data={
            'code': '200',
            'data': {'name': app_info.name,
                     'server_version': app_info.serverVersion,
                     'update_url': app_info.updateUrl,
                     'size': app_info.size,
                     'uuid': app_info.uuid,
                     'platform': platform,
                     'bundle_identifier': app_info.bundle_identifier,
                     'display_image_url': app_info.get_display_image_url(),
                     'qr_url': app_info.get_qrcode_url()},
            'message': 'success'
        })
