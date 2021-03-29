# -*- coding: utf-8 -*-

import threading
from mail_templated import EmailMessage

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("django")


class EmailThread(threading.Thread):

    def __init__(self, qrcode_url, app_info, platform, recipient_list):
        self.qrcode_url = qrcode_url
        self.app_info = app_info
        self.platform = platform
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        logger.info("开始发送邮件")

        message = EmailMessage('alps/send_email_temple.tpl',
                               {'appQRCodeURL': self.qrcode_url,
                                'appInfo': self.app_info,
                                'platform': self.platform}, 'wenshu.cai@cwens.com',
                               to=self.recipient_list)
        message.send()
        logger.info("邮件发送成功")


def send_template_mail(qrcode_url, app_info, platform, recipient_list):
    EmailThread(qrcode_url, app_info, platform, recipient_list).start()
