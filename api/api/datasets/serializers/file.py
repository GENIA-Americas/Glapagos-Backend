from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from api.datasets.enums import FileType


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[
        FileExtensionValidator(allowed_extensions=['csv', 'json', 'txt'],
                               message=_('Only CSV, TXT, and JSON files are allowed.'))
    ])
    public = serializers.BooleanField()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        valid_extensions = ['csv', 'txt', 'json']
        extension = attrs['file'].name.split('.')[-1]
        if extension not in valid_extensions:
            raise serializers.ValidationError({"detail": _('Only CSV, TXT, and JSON files are allowed.')})
        attrs['extension'] = FileType(extension)

        return attrs



