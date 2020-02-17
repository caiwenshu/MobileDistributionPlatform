# -*- coding: utf-8 -*-

# from .models_grayreleased import *

from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser

from django.db.models import Q

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


class AppEmailConfigAddApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        if not 'name' in request.data:
            raise APIException('request.data missing key "name"')

        if not 'email' in request.data:
            raise APIException('request.data missing key "email"')

        if not 'group' in request.data:
            raise APIException('request.data missing key "group"')

        name = request.data["name"]
        email = request.data["email"]
        group = request.data["group"]

        groups = MobileApplicationGroup.objects.filter(type=group)
        if len(groups) > 0:
            mobile_group = groups[0]
            email_configuration = EmailConfiguration(mobile_application_group=mobile_group, name=name, email=email)
            email_configuration.save()

            return JSONResponse(data={
                'code': '200',
                'data': None,
                'message': '保存成功',
            })

        else:
            return JSONResponse(data={
                'code': '500',
                'data': None,
                'message': 'cannot found groups , please check param.',
                'total': 0
            })

    def get(self, request, format=None):

        return Response(status=204)


# 邮件删除
class AppEmailConfigDeleteApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        if not 'id' in request.data:
            raise APIException('request.data missing key "id"')

        id = request.data["id"]

        models = EmailConfiguration.objects.filter(id=id)

        for group in models:
            group.delete()

        return JSONResponse(data={
            'code': '200',
            'data': {},
            'message': 'success'
        })

    def get(self, request, format=None):

        return Response(status=204)


# 下载页面新增
class ProductDownloadPageAddApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        path = None
        isDistribution = False
        root_html = "download.html"

        if not 'desc' in request.data:
            raise APIException('request.data missing key "desc"')

        if not 'group_type' in request.data:
            raise APIException('request.data missing key "group_type"')

        if 'isDistribution' in request.data:
            if request.data["isDistribution"] == "1":
                isDistribution = True

        if 'file' in request.data and request.data["file"] != "null":
            path = request.data["file"]
        else:
            return res_with_empty_data('文件地址必须存在')

        if 'root_html' in request.data:
            root_html = request.data['root_html'];

        desc = request.data["desc"]
        group_type = request.data["group_type"]

        mobile_groups = MobileApplicationGroup.objects.filter(type=group_type)

        if len(mobile_groups) > 0:

            mobile_group = mobile_groups[0]
            pm = DownloadPageConfiguration(name=desc,
                                           mobile_application_group=mobile_group,
                                           path=path,
                                           rootHtml=root_html,
                                           isDistribution=isDistribution, )
            pm.save()

            if pm.isDistribution == True:
                try:
                    htmls = DownloadPageConfiguration.objects.filter(isDistribution=True,
                                                                     mobile_application_group=mobile_group).exclude(
                        pk=pm.id)
                    for info in htmls:
                        info.isDistribution = False
                        info.save()

                except DownloadPageConfiguration.DoesNotExist:
                    print("ProductHtml.DoesNotExist.")

            return JSONResponse(data={
                'code': '200',
                'data': {},
                'message': 'success'
            })
        else:
            return res_with_empty_data('group_type 不存在')

    def get(self, request, format=None):

        return Response(status=204)


class AdminAddGroupApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        if not 'name' in request.data:
            raise APIException('request.data missing key "name"')

        if not 'type' in request.data:
            raise APIException('request.data missing key "type"')

        if not 'ios_bundle_identifier' in request.data:
            raise APIException('request.data missing key "ios_bundle_identifier"')

        if not 'android_bundle_identifier' in request.data:
            raise APIException('request.data missing key "android_bundle_identifier"')

        name = request.data["name"]
        type = request.data["type"]
        ios_bundle_identifier = request.data["ios_bundle_identifier"]
        android_bundle_identifier = request.data["android_bundle_identifier"]
        ios_name = name + "_" + settings.IOS
        android_name = name + "_" + settings.ANDROID

        from django.db.models import Q

        groups = MobileApplicationGroup.objects.filter(Q(type=type) | Q(name=name))

        ios = MobileApplication.objects.filter(bundle_identifier=ios_bundle_identifier, platform=settings.IOS)
        android = MobileApplication.objects.filter(bundle_identifier=android_bundle_identifier,
                                                   platform=settings.ANDROID)
        if len(ios) > 0:
            return res_with_empty_data('ios_bundle_identifier is exist. please check the bundle_identifier')

        if len(android) > 0:
            return res_with_empty_data('android_bundle_identifier is exist. please check the bundle_identifier')

        if len(groups) > 0:

            return res_with_empty_data('产品组名/产品组标示已经存在，请检查数据')

        else:

            app_group = MobileApplicationGroup(name=name, type=type)
            app_group.save()

            ios_application = MobileApplication(mobile_application_group=app_group,
                                                name=ios_name,
                                                platform=settings.IOS,
                                                bundle_identifier=ios_bundle_identifier)

            android_application = MobileApplication(mobile_application_group=app_group,
                                                    name=android_name,
                                                    platform=settings.ANDROID,
                                                    bundle_identifier=android_bundle_identifier)

            ios_application.save()
            android_application.save()

            return JSONResponse(data={
                'code': '200',
                'data': None,
                'message': '保存成功',
            })

    def get(self, request, format=None):

        return Response(status=204)


# Group删除
class AppGroupDeleteApiView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, format=None):

        if not 'type' in request.data:
            raise APIException('request.data missing key "type"')

        type = request.data["type"]

        models = MobileApplicationGroup.objects.filter(type=type)

        for group in models:
            group.delete()

        return JSONResponse(data={
            'code': '200',
            'data': {},
            'message': 'success'
        })

    def get(self, request, format=None):

        return Response(status=204)
