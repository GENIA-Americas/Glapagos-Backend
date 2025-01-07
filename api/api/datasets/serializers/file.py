import json
from typing import List

import magic
import pandas as pd

from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from api.datasets.services.upload_providers import return_url_provider
from api.datasets.models import File
from api.datasets.enums import FileType, UploadType
from api.datasets.utils import is_valid_column_name, create_dataframe_from_csv, create_dataframe_from_json, validate_csv_column_names
from api.datasets.exceptions import InvalidFileException


def validate_size(value: int):
    """
    Validates that the value isn't greater that
    the FILE_UPLOAD_LIMIT defined in settings.
    raises a Validation error otherwise

    this functions mustn't be use outside serializers or serializer fields
    """
    if value >= settings.FILE_UPLOAD_LIMIT:
        raise serializers.ValidationError(
            dict(detail=_("The file size is too large"))
        )


def validate_mimes(value: str):
    """
    Validates that the mimetype corresponds to the allowed mimetypes.
    raises a Validation error otherwise

    this functions mustn't be use outside serializers or serializer fields
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

    this functions mustn't be use outside serializers or serializer fields
    """
    valid_extensions = ["csv", "txt", "json", "jsonl"]
    if value not in valid_extensions:
        raise serializers.ValidationError(
            {"detail": _("Only CSV, TXT, and JSON files are allowed.")}
        )


def _columns_validate(df: pd.DataFrame, schema: List = None):
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
                    "detail": _(
                        "Column is required but contains null values:") + column_name + f". {suffix_message}"
                })
            if mode != "REPEATED":
                df_temp = df.dropna(subset=[actual_column_name])
                actual_type = str(df_temp[actual_column_name].dtype)

                base_message = _("Column should be of type")
                suffix_message = _("You must ensure that all rows are of this data type or modify the schema.")
                if expected_type == "INT64" and actual_type not in ["int64"]:
                    raise serializers.ValidationError(
                        {"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
                elif expected_type == "FLOAT64" and actual_type not in ["float64"]:
                    raise serializers.ValidationError(
                        {"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
                elif expected_type == "BOOLEAN" and actual_type not in ["bool"]:
                    raise serializers.ValidationError(
                        {"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
                elif expected_type == "DATETIME":
                    if not pd.to_datetime(df[actual_column_name], errors='coerce').notnull().all():
                        raise serializers.ValidationError(
                            {"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
                if expected_type == "ARRAY" and actual_type not in ["object"]:
                    raise serializers.ValidationError(
                        {"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})

    else:
        suffix_message = _(
            "Column names must start with a letter and can only contain alphanumeric characters. Modify the column names in the source file or in the schema."
        )
        invalid_columns = [col for col in df.columns if not is_valid_column_name(col)]
        if invalid_columns:
            raise serializers.ValidationError({
                "detail": _("Invalid column names in the file:") + ', '.join(
                    invalid_columns[:20]) + f". {suffix_message}"
            })


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=False)


class FilePreviewSerializer(serializers.Serializer):
    preview = serializers.JSONField()
    skip_leading_rows = serializers.IntegerField(required=False, allow_null=True)
    file_type = serializers.ChoiceField(choices=[(tag.value, tag.label) for tag in FileType])

    def validate(self, attrs):
        file_type = attrs.get('file_type')
        preview = attrs.get('preview')

        if file_type in ['csv', 'txt']:
            if not isinstance(preview, str):
                raise serializers.ValidationError({
                    'preview': _('The preview field must be a string for CSV or TXT files.')
                })

            lines = preview.strip().split("\n")
            if len(lines) < 2:
                raise serializers.ValidationError(
                    _("File content must have at least two lines.")
                )

        elif file_type in ['json', 'jsonl']:
            attrs['preview'] = json.dumps(preview)

        return attrs


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

            metadata = provider.service.get_file_metadata(url)
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
    file_type = serializers.ChoiceField(choices=[(tag.value, tag.label) for tag in FileType])


class CSVSerializer(serializers.Serializer):
    file = serializers.FileField()
    schema = serializers.ListField(required=False)
    autodetect = serializers.BooleanField(required=False)
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        file = attrs.get('file')
        schema = attrs.get('schema', [])

        df, csv_params = create_dataframe_from_csv(file)

        _columns_validate(df, schema)
        return attrs

class JSONSerializer(serializers.Serializer):
    file = serializers.FileField()
    schema = serializers.ListField(required=False)
    autodetect = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        file = attrs.get('file')
        schema = attrs.get('schema', [])

        df = create_dataframe_from_json(file)
        _columns_validate(df, schema)
        return attrs


class TXTSerializer(serializers.Serializer):
    file = serializers.FileField()


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    public = serializers.BooleanField()
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)
    autodetect = serializers.BooleanField(required=False)
    schema = serializers.ListField(required=False)
    file_type = serializers.ChoiceField(choices=[(tag.value, tag.label) for tag in FileType])
    url = ProviderUrlField(required=False)
    upload_type = serializers.ChoiceField(choices=UploadType.choices)
    description = serializers.CharField(max_length=200)

    def validate_file(self, value):
        try:
            content = value.read().decode('utf-8').splitlines()
        except UnicodeDecodeError as exp:
            raise InvalidFileException(error=str(exp))

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

            if isinstance(name, str) and is_valid_column_name(name):
                continue

            invalid_columns.append(name)

        if invalid_columns:
            invalid_columns_str = ', '.join(invalid_columns)
            raise serializers.ValidationError({
                "detail": _("Invalid column names: {invalid_columns}").format(invalid_columns=invalid_columns_str)
            })

        return value_obj

    def validate(self, attrs):
        attrs = super().validate(attrs)
        file_type = attrs.get('file_type')
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

            serializer_class_name = f"{file_type.upper()}Serializer"
            serializer_class = globals().get(serializer_class_name)

            if serializer_class:
                data = dict(
                    file=attrs["file"],
                    schema=attrs.get("schema", []),
                    autodetect=attrs.get("autodetect", False),
                )
                serializer_class(data=data).is_valid(raise_exception=True)

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
