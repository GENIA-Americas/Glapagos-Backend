import magic
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.datasets.models import File
from api.datasets.enums import FileType
from api.datasets.models.table import Table


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField()


class FilePreviewSerializer(serializers.Serializer):
    preview = serializers.CharField()

    def validate_preview(self, value):
        lines = value.strip().split("\n")
        if len(lines) < 2:
            raise serializers.ValidationError(
                _("File content must have at least two lines.")
            )
        return value


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    public = serializers.BooleanField()
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)
    autodetect = serializers.BooleanField(required=False)
    schema = serializers.ListField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        file = attrs["file"]
        valid_extensions = ["csv", "txt", "json"]
        valid_mime_types = ["text/csv", "application/json", "text/plain"]

        extension = attrs["file"].name.lower().split(".")[-1]
        if extension not in valid_extensions:
            raise serializers.ValidationError(
                {"detail": _("Only CSV, TXT, and JSON files are allowed.")}
            )

        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file.read(1024))
        file.seek(0)

        if mime_type not in valid_mime_types:
            raise serializers.ValidationError(
                {"detail": _("The filetype does not match with the extension")}
            )

        attrs["extension"] = FileType(extension)

        if extension == "csv":
            if attrs["skip_leading_rows"] is None or attrs["schema"] is None:
                raise serializers.ValidationError(
                    {
                        "detail": _(
                            "Unable to determine the file schema due to missing or incomplete parameters."
                        )
                    }
                )

        return attrs


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"
