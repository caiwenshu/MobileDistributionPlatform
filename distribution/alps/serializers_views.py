# -*- coding: utf-8 -*-

from .models import *
from rest_framework import serializers
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.sites.models import Site
from .utils import parse_to_url_http
import os
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("django")


# Serializers define the API representation.
class IOSAppInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IOSAppInfo
        fields = ('serverVersion',
                  'updateUrl',
                  'serviceUpdateMsg',
                  'createTime',
                  'isDistribution',
                  'size',
                  'historyDistribution',
                  'isPreDistribution',
                  'forceOnline',
                  'isSendRemoteServer',
                  'uuid',
                  'id'),

    # def upload_link(self, obj):
    #     if obj.path:
    #         send_remote_server = str(reverse('alps:send_remoteserver', kwargs={'app_id': str(obj.uuid)}))
    #         return parse_to_url_http(send_remote_server)
    #
    #     else:
    #         return None

    def app_preview_link(self, obj):
        if obj.path:
            preview_app = str(reverse('alps:preview_app', kwargs={'app_id': str(obj.uuid)}))
            return parse_to_url_http(preview_app)
        else:
            return None

    def app_send_email(self, obj):
        if obj.path:
            send_email = str(reverse('alps:send_email', kwargs={'app_id': str(obj.uuid)}))
            return parse_to_url_http(send_email)
            #  ("preview", str(obj.uuid))
        else:
            return None

    def to_representation(self, obj):

        return {
            'id': obj.id,
            'name': obj.name,
            'serverVersion': obj.serverVersion,
            'versionCode': obj.versionCode,
            'updateUrl': obj.updateUrl,
            'serviceUpdateMsg': obj.serviceUpdateMsg,
            'createTime': timezone.localtime(obj.createTime).strftime('%Y-%m-%d %H:%m:%S'),
            'isDistribution': obj.isDistribution,
            'size': obj.size,
            'historyDistribution': obj.historyDistribution,
            'isPreDistribution': obj.isPreDistribution,
            'forceOnline': obj.forceOnline,
            'uuid': obj.uuid,
            'isSendRemoteServer': obj.isSendRemoteServer,
            'bundle_identifier': obj.bundle_identifier,
            # 'upload_link': self.upload_link(obj),
            'app_preview_link': self.app_preview_link(obj),
            'app_send_email': self.app_send_email(obj)
        }
    # def get_alternate_serverVersion(self, obj):
    #     return obj.serverVersion


class AndroidAppInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AndroidAppInfo
        fields = ('serverVersion',
                  'updateUrl',
                  'serviceUpdateMsg',
                  'createTime',
                  'isDistribution',
                  'size',
                  'historyDistribution',
                  'isPreDistribution',
                  'forceOnline',
                  'uuid',
                  'isSendRemoteServer',
                  'id'),

    # def upload_link(self, obj):
    #     if obj.path:
    #         send_remote_server = str(reverse('alps:send_remoteserver', kwargs={'app_id': str(obj.uuid)}))
    #         return parse_to_url_http(send_remote_server)
    #
    #     else:
    #         return None

    def app_preview_link(self, obj):
        if obj.path:
            preview_app = str(reverse('alps:preview_app', kwargs={'app_id': str(obj.uuid)}))
            return parse_to_url_http(preview_app)
        else:
            return None

    def app_send_email(self, obj):
        if obj.path:
            send_email = str(reverse('alps:send_email', kwargs={'app_id': str(obj.uuid)}))
            return parse_to_url_http(send_email)
            #  ("preview", str(obj.uuid))
        else:
            return None

    def to_representation(self, obj):

        return {
            'id': obj.id,
            'name': obj.name,
            'serverVersion': obj.serverVersion,
            'versionCode': obj.versionCode,
            'updateUrl': obj.updateUrl,
            'serviceUpdateMsg': obj.serviceUpdateMsg,
            'createTime': obj.createTime.strftime('%Y-%m-%d %H:%m:%S'),
            'isDistribution': obj.isDistribution,
            'size': obj.size,
            'historyDistribution': obj.historyDistribution,
            'isPreDistribution': obj.isPreDistribution,
            'forceOnline': obj.forceOnline,
            'uuid': obj.uuid,
            'isSendRemoteServer': obj.isSendRemoteServer,
            'bundle_identifier': obj.bundle_identifier,
            # 'upload_link': self.upload_link(obj),
            'app_preview_link': self.app_preview_link(obj),
            'app_send_email': self.app_send_email(obj)
        }


class DownloadPageConfigurationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DownloadPageConfiguration
        fields = ('name',
                  'mobile_application_group',
                  'path',
                  'rootHtml',
                  'isDistribution',
                  'id'),

    def visit_link(self, obj):
        if obj.path:

            r_html = "index.html"
            if not obj.rootHtml == "":
                r_html = obj.rootHtml
            file_dir = os.path.dirname(obj.path.url)
            full_path = file_dir + "/" + r_html

            # send_remote_server = str("/alps" + full_path)
            return parse_to_url_http(full_path)

        else:
            return None

    def to_representation(self, obj):

        return {
            'id': obj.id,
            'name': obj.name,
            'mobile_application_group': obj.mobile_application_group.name,
            'rootHtml': obj.rootHtml,
            'isDistribution': obj.isDistribution,
            'path': parse_to_url_http(obj.path.url),
            'url': self.visit_link(obj),
        }


class EmailConfigurationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmailConfiguration
        fields = ('name',
                  'mobile_application_group',
                  'email',
                  'environment',
                  'id'),

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'environment': obj.environment,
            'mobile_application_group': obj.mobile_application_group.name,
            'email': obj.email,
        }
