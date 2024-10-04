from rest_framework import serializers

from .file import FileSerializer
from api.datasets.enums import TransformationOption
from api.datasets.models import Table


class TableSerializer(serializers.ModelSerializer):
    file = FileSerializer()

    class Meta:
        model = Table
        fields = ['id', 'name', 'created', 'modified', 'dataset_name', 'data_expiration',
                  'number_of_rows', 'total_logical_bytes', 'reference_name', 'path', 'file', 'owner']


class SingleTransformSerializer(serializers.Serializer):
    field = serializers.CharField()
    transformation = serializers.ChoiceField(choices=[(tag.value, tag.name) for tag in TransformationOption])


class TableTransformSerializer(serializers.Serializer):
    create_table = serializers.BooleanField()
    transformations = serializers.ListSerializer(child=SingleTransformSerializer())

