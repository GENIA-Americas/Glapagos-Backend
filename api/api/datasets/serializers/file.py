import json
import re
import magic
import pandas as pd

from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from api.datasets.services.upload_providers import return_url_provider
from api.datasets.models import File
from api.datasets.enums import FileType, UploadType
from api.datasets.utils import create_dataframe_from_csv, validate_csv_column_names


def validate_size(value: int):
    """
    Validates that the value isn't grater that 
    the FILE_UPLOAD_LIMIT defined in settings.
    raises a Validation error otherwise

    this fuctions mustn't be use outside serializers or serializer fields
    """
    if value >= settings.FILE_UPLOAD_LIMIT: 
        raise serializers.ValidationError(
            dict(detail=_("The file size is too large"))
        )

def validate_mimes(value: str):
    """
    Validates that the mimetype corresponds to the allowed mimetypes.
    raises a Validation error otherwise

    this fuctions mustn't be use outside serializers or serializer fields
    """
    valid_mime_types = ["text/csv", "application/json", "text/plain"]
    if value not in valid_mime_types:
        raise serializers.ValidationError(
            {"detail": _("The filetype does not match with the extension")}
        )

def validate_extension(value: str):
    """
    Validates that the extension corresponds to the allowed extensions.
    raises a Validation error otherwise

    this fuctions mustn't be use outside serializers or serializer fields
    """
    valid_extensions = ["csv", "txt", "json"]
    if value not in valid_extensions:
        raise serializers.ValidationError(
            {"detail": _("Only CSV, TXT, and JSON files are allowed.")}
        )


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField()


class FilePreviewSerializer(serializers.Serializer):
    preview = serializers.CharField()
    skip_leading_rows = serializers.IntegerField()

    def validate_preview(self, value):
        lines = value.strip().split("\n")
        if len(lines) < 2:
            raise serializers.ValidationError(
                _("File content must have at least two lines.")
            )
        return value


class ProviderUrlField(serializers.URLField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        url = data 
        provider = return_url_provider(url)

        if provider.service.is_folder(url):
            files = provider.service.list_files(url)

            extension = ""
            for i in files:
                name = i.get("name", "").split(".")[-1]
                validate_extension(name)

                if extension == "":
                    extension = name

                if extension != name:
                    raise serializers.ValidationError(
                        dict(detail=_("Invalid extension, all files should have the same file extension"))
                    )

            size = 0
            for i in files:
                size += int(i.get("size", 0))
            validate_size(size)

            mimetype = ""
            for i in files:
                mime =  i.get("mimeType", "")
                if mimetype == "":
                    mimetype = mime 

                if mime != mimetype:
                    raise serializers.ValidationError(
                        dict(detail=_("Invalid mimetype, all files should have the same mimetype"))
                    )
            validate_mimes(mimetype)

        else:

            metadata = provider.service.get_file_metadata(url, ["size", "name", "mimeType"])
            size = int(metadata.get("size", 0))
            validate_size(size)
            validate_mimes(metadata.get("mimeType", ""))

            extension = metadata.get("name", "").split(".")[-1]
            if extension not in FileType.values:
                raise serializers.ValidationError(
                    {"detail": _("Only CSV, TXT, and JSON files are allowed.")}
                )

        self.extension = extension
        return value


class UrlPreviewSerializer(serializers.Serializer):
    url = ProviderUrlField(allow_blank=False)


class CSVSerializer(serializers.Serializer):
    file = serializers.FileField()
    schema = serializers.ListField(required=False)
    autodetect = serializers.BooleanField(required=False)
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        file = attrs.get('file')
        schema = attrs.get('schema', [])
        autodetect = attrs.get('autodetect', False)

        try:
            df, csv_params = create_dataframe_from_csv(file)
        except Exception:
            raise serializers.ValidationError({"detail": _("Error reading CSV file")})

        if autodetect:
            validate_csv_column_names(df)

        if schema:
            if len(schema) != len(df.columns):
                raise serializers.ValidationError({"detail": _(
                    "The number of columns in the schema does not match the number of columns in the CSV file."
                )})

        for idx, item in enumerate(schema):
            column_name = item['column_name']
            expected_type = item['data_type']
            mode = item.get('mode', 'NULLABLE')

            actual_column_name = df.columns[idx]

            if mode == "REQUIRED" and df[actual_column_name].isnull().any():
                suffix_message = _("You must indicate in the schema that the column can accept null values.")
                raise serializers.ValidationError({
                    "detail": _("Column is required but contains null values:") + column_name + f". {suffix_message}"
                })

            df_temp = df.dropna(subset=[actual_column_name])
            actual_type = str(df_temp[actual_column_name].dtype)

            base_message = _("Column should be of type")
            suffix_message = _("You must ensure that all rows are of this data type or modify the schema.")
            if expected_type == "STRING" and actual_type not in ["object", "string"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "INT64" and actual_type not in ["int64"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "FLOAT64" and actual_type not in ["float64"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "BOOLEAN" and actual_type not in ["bool"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "DATETIME":
                if not pd.to_datetime(df[actual_column_name], errors='coerce').notnull().all():
                    raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})

        return attrs


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    public = serializers.BooleanField()
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)
    autodetect = serializers.BooleanField(required=False)
    schema = serializers.ListField(required=False)

    url = ProviderUrlField(required=False)
    upload_type = serializers.ChoiceField(choices=UploadType.choices)

    def validate_file(self, value):
        content = value.read().decode('utf-8').splitlines()
        if content[-1].strip() == '':
            raise serializers.ValidationError({"detail": _("You must remove the blank rows at the end of the file.")})
        value.seek(0)
        return value

    def validate_schema(self, value):
        value_obj = []
        if isinstance(value, list) and len(value) == 1:
            try:
                value_obj = json.loads(value[0])
            except json.JSONDecodeError:
                raise serializers.ValidationError({"detail": _("Invalid JSON format in schema.")})

        invalid_columns = []
        for item in value_obj:
            name = item.get('column_name')

            if isinstance(name, str) and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                continue

            invalid_columns.append(name)

        if invalid_columns:
            invalid_columns_str = ', '.join(invalid_columns)
            raise serializers.ValidationError({"detail": _("Invalid column names:") + invalid_columns_str})

        return value_obj

    def validate(self, attrs):
        attrs = super().validate(attrs)

        upload_type = attrs.get('upload_type')
        extension = ""

        if not attrs.get('autodetect') and not attrs.get('schema'):
            raise serializers.ValidationError({"detail": _(
                "Unable to determine the file schema due to missing or incomplete parameters."
            )})

        if attrs.get('autodetect') and attrs.get('schema'):
            raise serializers.ValidationError({"detail": _(
                "Schema autodetection cannot be used simultaneously with a provided schema."
            )})

        if attrs.get('upload_type') == UploadType.FILE and not attrs.get('file'):
            raise serializers.ValidationError({"detail": _(
                "File was not found for upload_type file"
            )})

        if attrs.get('upload_type') == UploadType.URL and not attrs.get('url'):
            raise serializers.ValidationError({"detail": _(
                "Url was not found for upload_type url"
            )})

        if upload_type == UploadType.FILE:
            file = attrs["file"]

            extension = attrs["file"].name.lower().split(".")[-1]
            validate_extension(extension)
            attrs['extension'] = FileType(extension)

            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file.read(4096))
            file.seek(0)
            validate_mimes(mime_type)

            if extension == 'csv':
                csv_data = dict(
                    file=attrs["file"], 
                    schema=attrs.get("schema", []), 
                    autodetect=attrs.get("autodetect", False), 
                )
                CSVSerializer(data=csv_data).is_valid(raise_exception=True)

        elif upload_type == UploadType.URL:
            extension = self.fields.get('url').extension

        if attrs.get('skip_leading_rows') is None and extension == "csv":
            raise serializers.ValidationError({"detail": _(
                "Missing or incomplete parameters for CSV files."
            )})

        attrs["extension"] = extension
        return attrs


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"
