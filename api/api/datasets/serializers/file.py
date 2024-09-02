from rest_framework import serializers
from api.datasets.enums import FileType


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    public = serializers.BooleanField()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        valid_extensions = ['csv', 'txt', 'json']
        extension = attrs['file'].name.split('.')[-1]
        if extension not in valid_extensions:
            raise serializers.ValidationError({"detail": "invalid extension"})
        attrs['extension'] = FileType(extension)

        return attrs



