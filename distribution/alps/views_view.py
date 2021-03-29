# -*- coding: utf-8 -*-

from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser

# from .models_rn import *
from .serializers_views import *
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("django")


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def res_with_empty_data(message):
    return JSONResponse(status=200, data={
        'code': '500',
        'data': {
        },
        'message': message
    })


class MobileApplicationGroupSearchApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    # parser_classes = (FormParser,)

    def get(self, request, format=None):
        mobile_application_group = MobileApplicationGroup.objects.all()

        return_dic = []

        for application_group in mobile_application_group:
            group_name = application_group.name
            group_type = application_group.type

            return_dic.append({"group_name": group_name,
                               "group_type": group_type
                               })

        # for application in mobile_applications:

        return JSONResponse(data={
            'code': '200',
            'data': return_dic,
            'message': 'success'
        })


# app 列表按条件查询
# {
#     "code": "200",
#     "data": [
#         {
#             "group_name": "groupname",
#             "group_type": "grouptype",
#             "ios_app": {
#                 "version": "3.34.0",
#                 "updatedate": "2018-10-10 14:00:00"
#             },
#             "android_app": {
#                 "version": "3.34.0",
#                 "updatedate": "2018-10-10 14:00:00"
#             }
#         },
#         ...
#     ],
#     "message": "success"
# }
#
class MobileApplicationSearchApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    # parser_classes = (FormParser,)

    def get(self, request, format=None):

        mobile_application_group = MobileApplicationGroup.objects.all()

        return_dic = []

        for application_group in mobile_application_group:

            group_name = application_group.name
            group_type = application_group.type
            display_icon = ""
            try:
                app_info = AndroidAppInfo.objects.filter(isDistribution=True,
                                                         mobile_application__mobile_application_group=application_group)

                if len(app_info) > 0:
                    info = app_info[0]
                    server_version = info.serverVersion
                    time = info.createTime.strftime('%Y-%m-%d %H:%m')
                    android_dic = {
                        "version": server_version,
                        "time": time,
                        "application_id": info.mobile_application.uuid
                    }
                    display_icon = info.get_display_image_url()
                else:
                    android_dic = None
            except AndroidAppInfo.DoesNotExist:
                android_dic = None
                print("AndroidAppInfoAdmin.DoesNotExist.")

            try:

                app_info = IOSAppInfo.objects.filter(isDistribution=True,
                                                     mobile_application__mobile_application_group=application_group)

                if len(app_info) > 0:
                    info = app_info[0]
                    server_version = info.serverVersion
                    time = info.createTime.strftime('%Y-%m-%d %H:%m')
                    ios_dic = {
                        "version": server_version,
                        "time": time,
                        "application_id": info.mobile_application.uuid
                    }
                    display_icon = info.get_display_image_url()
                else:
                    ios_dic = None
            except AndroidAppInfo.DoesNotExist:
                ios_dic = None
                print("AndroidAppInfoAdmin.DoesNotExist.")

            #
            return_dic.append({"group_name": group_name,
                               "group_type": group_type,
                               "android_app": android_dic,
                               "ios_app": ios_dic,
                               "icon": display_icon
                               })

        # for application in mobile_applications:

        return JSONResponse(data={
            'code': '200',
            'data': return_dic,
            'message': 'success'
        })


class AppSearchApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        application_id = ""
        page_no = 0
        page_size = 2
        jira_version = ""

        if not 'applicationId' in request.data:
            raise APIException('request.data missing key "applicationId"')

        if 'pageNo' in request.data:
            page_no = int(request.data["pageNo"])

        if 'pageSize' in request.data:
            page_size = int(request.data["pageSize"])

        if 'applicationId' in request.data:
            application_id = request.data["applicationId"]

        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        is_distribution = False
        is_pre_distribution = False

        sql_page_no = page_no * page_size
        sql_page_size = (page_no + 1) * page_size
        applications = MobileApplication.objects.filter(uuid=application_id)

        if len(applications) > 0:
            application = applications.first()
            display_icon = ""
            platform = application.platform
            if platform == settings.IOS:
                count = IOSAppInfo.objects.filter(mobile_application=application).count()
                apps = IOSAppInfo.objects.filter(mobile_application=application).order_by('-id')[
                       sql_page_no: sql_page_size]
                if len(apps) > 0:
                    info = apps[0]
                    display_icon = info.get_display_image_url()
                app_info_serializer = IOSAppInfoSerializer(apps, many=True).data
            else:
                count = AndroidAppInfo.objects.filter(mobile_application=application).count()
                apps = AndroidAppInfo.objects.filter(mobile_application=application).order_by('-id')[
                       sql_page_no: sql_page_size]
                if len(apps) > 0:
                    info = apps[0]
                    display_icon = info.get_display_image_url()
                app_info_serializer = AndroidAppInfoSerializer(apps, many=True).data

            group_name = application.mobile_application_group.name
            group_type = application.mobile_application_group.type

            return_data = {"group_name": group_name,
                           "group_type": group_type,
                           "platform": application.platform,
                           "icon": display_icon,
                           "apps": app_info_serializer
                           }
            return JSONResponse(data={
                'code': '200',
                'data': return_data,
                'message': 'success',
                'total': count
            })
        else:
            return JSONResponse(data={
                'code': '500',
                'data': None,
                'message': 'application id is error.',
                'total': 0
            })

    def get(self, request, format=None):

        return Response(status=204)


class AppDownloadPageSearchApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        application_id = ""
        page_no = 0
        page_size = 2
        jira_version = ""

        if not 'groupType' in request.data:
            raise APIException('request.data missing key "groupType"')

        if 'pageNo' in request.data:
            page_no = int(request.data["pageNo"])

        if 'pageSize' in request.data:
            page_size = int(request.data["pageSize"])

        if 'groupType' in request.data:
            group_type = request.data["groupType"]

        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        is_distribution = False
        is_pre_distribution = False

        sql_page_no = page_no * page_size
        sql_page_size = (page_no + 1) * page_size
        groups = MobileApplicationGroup.objects.filter(type=group_type)
        if len(groups) > 0:
            mobile_application_group = groups.first()
            count = DownloadPageConfiguration.objects.filter(mobile_application_group=mobile_application_group).count()

            apps = DownloadPageConfiguration.objects.filter(mobile_application_group=mobile_application_group).order_by(
                '-id')[sql_page_no: sql_page_size]

            app_info_serializer = DownloadPageConfigurationSerializer(apps, many=True).data

            # print(app_info_serializer)

            group_name = mobile_application_group.name
            group_type = mobile_application_group.type

            return_data = {"group_name": group_name,
                           "group_type": group_type,
                           "pages": app_info_serializer
                           }

            return JSONResponse(data={
                'code': '200',
                'data': return_data,
                'message': 'success',
                'total': count
            })
        else:
            return JSONResponse(data={
                'code': '500',
                'data': None,
                'message': 'application id is error.',
                'total': 0
            })

    def get(self, request, format=None):

        return Response(status=204)


class AppEmailConfigSearchApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        application_id = ""
        page_no = 0
        page_size = 2
        jira_version = ""

        if not 'groupType' in request.data:
            raise APIException('request.data missing key "groupType"')

        if 'pageNo' in request.data:
            page_no = int(request.data["pageNo"])

        if 'pageSize' in request.data:
            page_size = int(request.data["pageSize"])

        if 'groupType' in request.data:
            group_type = request.data["groupType"]

        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        # application_id = "e68ba672-4dc0-4031-a49a-e77fa7155dee"
        is_distribution = False
        is_pre_distribution = False

        sql_page_no = page_no * page_size
        sql_page_size = (page_no + 1) * page_size
        groups = MobileApplicationGroup.objects.filter(type=group_type)

        if len(groups) > 0:
            mobile_application_group = groups.first()

            count = EmailConfiguration.objects.filter(mobile_application_group=mobile_application_group).count()

            apps = EmailConfiguration.objects.filter(mobile_application_group=mobile_application_group).order_by('-id')[
                   sql_page_no: sql_page_size]

            app_info_serializer = EmailConfigurationSerializer(apps, many=True).data

            # print(app_info_serializer)

            group_name = mobile_application_group.name
            group_type = mobile_application_group.type

            return_data = {"group_name": group_name,
                           "group_type": group_type,
                           "emails": app_info_serializer
                           }

            return JSONResponse(data={
                'code': '200',
                'data': return_data,
                'message': 'success',
                'total': count
            })

        else:
            return JSONResponse(data={
                'code': '500',
                'data': None,
                'message': 'application id is error.',
                'total': 0
            })

    def get(self, request, format=None):

        return Response(status=204)

from django.contrib.sites.models import Site


# 编辑设置
class AppSettingsApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        if 'domain' in request.data:
            domain = request.data["domain"]

        if 'name' in request.data:
            name = request.data["name"]

        current_site = Site.objects.get_current()
        current_site.domain = domain
        current_site.name = name
        current_site.save()

        return JSONResponse(data={
                'code': '200',
                'data': None,
                'message': 'success'
        })

    def get(self, request, format=None):

        return Response(status=204)


# 编辑设置
class AppGetSettingsApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        current_site = Site.objects.get_current()

        return JSONResponse(data={
                'code': '200',
                'data': {
                    'domain': current_site.domain,
                    'name': current_site.name
                },
                'message': 'success'
        })

    def get(self, request, format=None):

        return Response(status=204)