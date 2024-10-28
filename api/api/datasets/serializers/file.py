import json

import magic
import pandas as pd
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.datasets.models import File
from api.datasets.enums import FileType
from api.datasets.utils import is_valid_column_name, create_dataframe_from_csv
from api.datasets.exceptions import InvalidFileException


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField()


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

        elif file_type == 'json':
            attrs['preview'] = json.dumps(preview)

        return attrs


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    public = serializers.BooleanField()
    skip_leading_rows = serializers.IntegerField(min_value=0, required=False)
    autodetect = serializers.BooleanField(required=False)
    schema = serializers.ListField(required=False)

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

    def csv_validate(self, attrs):
        file = attrs.get('file')
        schema = attrs.get('schema', [])
        autodetect = attrs.get('autodetect', False)

        df, csv_params = create_dataframe_from_csv(file)

        if autodetect:
            suffix_message = _("Column names must start with a letter and can only contain alphanumeric characters. Modify the column names in the source file or in the schema.")
            invalid_columns = [col for col in df.columns if not is_valid_column_name(col)]
            if invalid_columns:
                raise serializers.ValidationError({
                    "detail": _("Invalid column names in CSV:") + ', '.join(invalid_columns) + f". {suffix_message}"
                })

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
            if expected_type == "INT64" and actual_type not in ["int64"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "FLOAT64" and actual_type not in ["float64"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "BOOLEAN" and actual_type not in ["bool"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            elif expected_type == "DATETIME":
                if not pd.to_datetime(df[actual_column_name], errors='coerce').notnull().all():
                    raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
            if expected_type == "ARRAY" and actual_type not in ["object"]:
                raise serializers.ValidationError({"detail": f"{base_message} {expected_type}: {column_name}. {suffix_message}"})
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
        mime_type = mime.from_buffer(file.read(4096))
        file.seek(0)

        if mime_type not in valid_mime_types:
            raise serializers.ValidationError(
                {"detail": _("The filetype does not match with the extension")}
            )

        if attrs.get('skip_leading_rows') is None:
            raise serializers.ValidationError({"detail": _(
                "Missing or incomplete parameters for CSV files."
            )})

        if not attrs.get('autodetect') and not attrs.get('schema'):
            raise serializers.ValidationError({"detail": _(
                "Unable to determine the file schema due to missing or incomplete parameters."
            )})

        if attrs.get('autodetect') and attrs.get('schema'):
            raise serializers.ValidationError({"detail": _(
                "Schema autodetection cannot be used simultaneously with a provided schema."
            )})

        attrs['extension'] = FileType(extension)

        if extension == 'csv':
            self.csv_validate(attrs)

        return attrs


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"
