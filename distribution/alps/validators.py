import os
from django.core.exceptions import ValidationError


def validate_apk_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.apk']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')


def validate_ipa_extension(value):
    # print(value)
    # print(value.url)
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.ipa']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')
