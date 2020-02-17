# -*- coding: utf-8 -*-

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'code': '200',
            'data': {
                'token': token.key,
                'user_id': user.pk,
                'email': user.email
            },
            'message': '登录成功'
        })
