import magic
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from api.datasets.enums import FileType


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    public = serializers.BooleanField()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        file = attrs['file']
        valid_extensions = ['csv', 'txt', 'json']
        valid_mime_types = ['text/csv', 'application/json', 'text/plain']

        extension = attrs['file'].name.lower().split('.')[-1]
        if extension not in valid_extensions:
            raise serializers.ValidationError({"detail": _('Only CSV, TXT, and JSON files are allowed.')})

        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file.read(1024))
        file.seek(0)

        if mime_type not in valid_mime_types:
            raise serializers.ValidationError({"detail": _('The filetype does not match with the extension')})

        attrs['extension'] = FileType(extension)

        return attrs



