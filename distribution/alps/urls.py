# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views, views_view, views_view_add

from . import auth_token

app_name = 'alps'

urlpatterns = [
    # url(r'^(?P<gp>[0-9a-z-]+)/appversion.json', views_grayreleased.app_version, name='app_version'),
    # url(r'^(?P<gp>[0-9a-z-]+)/applaunch.json', views_functionlaunch.app_launch, name='app_launch'),
    # url(r'^download.html', views.download_distribution, name='download_distribution'),
    url(r'^send_email/(?P<app_id>[0-9a-z-]+)/$', views.send_email, name='send_email'),
    url(r'^preview/(?P<app_id>[0-9a-z-]+)/$', views.preview_app, name='preview_app'),
    # url(r'^send_remoteserver/(?P<app_id>[0-9a-z-]+)/$', views.send_remoteserver, name='send_remoteserver'),
    url(r'^send_apk/(?P<app_id>[0-9a-z-]+)/$', views.send_apk, name='send_apk'),
    url(r'^plist/(?P<app_id>[0-9a-z-]+)\.plist$', views.ios_app_plist, name='ios_app_plist'),
    url(r'^upload', views.UploadFileApiView.as_view(), name='upload_file'),
    url(r'^generate_qrcode/(?P<app_id>[0-9a-z-]+).png$', views.generate_qrcode, name='generate_qrcode'),
    # 动态下载页
    url(r'^download/(?P<type>[0-9a-z-]+)/$', views.dynamic_download_distribution, name='dynamic_download_distribution'),
    # 根据请求头，返回版本信息
    url(r'^info/(?P<tp>[0-9a-z-]+)/$', views.application_information, name='application_information'),

    # android lint 分析详情
    # url(r'^android_lint_detail/(?P<android_lint_summary_id>[0-9a-z-]+)', views_quality.preview_android_lint_detail,
    #     name='preview_android_lint_detail'),

    # 提供接口给web
    # 只包含group
    url(r'^admin_group_list', views_view.MobileApplicationGroupSearchApiView.as_view(), name='admin_group_list'),
    # 包含group下最新的ios 和 android 版本
    url(r'^admin_group', views_view.MobileApplicationSearchApiView.as_view(), name='admin_group'),
    url(r'^admin_app_list', views_view.AppSearchApiView.as_view(), name='admin_app_list'),
    url(r'^admin_app_download_list', views_view.AppDownloadPageSearchApiView.as_view(), name='admin_app_download_list'),
    url(r'^admin_app_email_config_list', views_view.AppEmailConfigSearchApiView.as_view(),
        name='admin_app_email_config_list'),
    url(r'^admin_add_group', views_view_add.AdminAddGroupApiView.as_view(), name='admin_add_group'),
    url(r'^admin_add_email', views_view_add.AppEmailConfigAddApiView.as_view(), name='admin_add_email'),
    url(r'^admin_delete_email', views_view_add.AppEmailConfigDeleteApiView.as_view(), name='admin_delete_email'),
    url(r'^admin_add_download', views_view_add.ProductDownloadPageAddApiView.as_view(), name='admin_add_download'),
    url(r'^admin_remove_group', views_view_add.AppGroupDeleteApiView.as_view(), name='admin_remove_group'),
    url(r'^admin_save_settings', views_view.AppSettingsApiView.as_view(), name='admin_save_settings'),
    url(r'^admin_get_settings', views_view.AppGetSettingsApiView.as_view(), name='admin_get_settings'),

    url(r'^api-token-auth', auth_token.CustomAuthToken.as_view()),

    # 触发页面
    # url(r'^trigger_cron.html', views_cron.trigger_cron_html, name='trigger_cron_html'),

    # 更新发布信息
    url(r'^update_distribution_info', views.UpdateAppDistrubutionApiView.as_view(), name='upload_distribution_apiview'),

    url(r'^get_distribution_info', views.GetAppDistributionApiView.as_view(), name='get_distribution_apiview'),

]
