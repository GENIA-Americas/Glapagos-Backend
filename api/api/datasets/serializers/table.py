from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .file import FileSerializer
from api.datasets.enums import TransformationOption
from api.datasets.models import Table
from api.users.models import User


class TableSerializer(serializers.ModelSerializer):
    file = FileSerializer()

    class Meta:
        model = Table
        fields = ['id', 'name', 'created', 'modified', 'dataset_name', 'number_of_rows',
                  'total_logical_bytes', 'reference_name', 'path', 'file', 'owner', 'public']


class OptionSerializer(serializers.Serializer):
    convert_to = serializers.CharField(required=False)
    text_case = serializers.CharField(required=False)

    def validate_convert_to(self, value):
        data_types = ["INT64", "FLOAT64", "DATETIME", "DATE", "STRING"]
        if value.upper() not in data_types:
            raise serializers.ValidationError({"detail": _("Invalid format to convert")})
        return value.upper()

    def validate_text_case(self, value):
        valid_cases = ["LOWER", "UPPER"]
        if value.upper() not in valid_cases:
            raise serializers.ValidationError({"detail": _("Invalid format to convert")})
        return value.upper()


class SingleTransformSerializer(serializers.Serializer):
    field = serializers.CharField()
    transformation = serializers.ChoiceField(choices=[(tag.value, tag.name) for tag in TransformationOption])
    options = OptionSerializer(required=False)

    def validate(self, attrs):
        transformation = attrs.get("transformation")
        options = attrs.get("options")
        if transformation == TransformationOption.DATA_TYPE_CONVERSION.value and (
                not options or not options.get("convert_to")):
            raise serializers.ValidationError(
                _("'{option}' is a mandatory field for {transformation} transformation").format(
                    option='convert_to', transformation=transformation
                )
            )
        elif transformation == TransformationOption.STANDARDIZING_TEXT.value and (
                not options or not options.get("text_case")):
            raise serializers.ValidationError(
                _("'{option}' is a mandatory field for {transformation} transformation").format(
                    option='text_case', transformation=transformation
                )
            )
        return attrs


class TableTransformSerializer(serializers.Serializer):
    create_table = serializers.BooleanField()
    public_destination = serializers.BooleanField(required=False)
    transformations = serializers.ListSerializer(child=SingleTransformSerializer())

    def validate(self, attrs):
        create_table: bool = attrs.get('create_table')
        public_destination: bool = attrs.get('public_destination')
        table: Table = self.context.get('table')
        user: User = self.context.get('user')

        is_owner = table.owner == user

        if not is_owner:
            if not table.public:
                raise serializers.ValidationError(
                    _("You do not have permission to transform this table because you are not the owner and the table is not public.")
                )
            elif not create_table:
                raise serializers.ValidationError(
                    _("You do not have permission to modify the original table, and creating a new table has not been requested.")
                )

        if create_table and public_destination is None:
            raise serializers.ValidationError(
                _("If you want to create a new table, you must specify its privacy setting.")
            )

        return attrs


class TableSchemaSerializer(serializers.Serializer):
    field = serializers.CharField(required=False, allow_blank=True)

    def validate_field(self, value):
        table = self.context.get('table')

        for row in table.schema:
            if row.get('column_name') == value:
                return value

        raise serializers.ValidationError(_("Field '{field}' does not exist in the dataset schema").format(field=value))
