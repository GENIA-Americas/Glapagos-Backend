from rest_framework import serializers

from api.datasets.models import Table
from .file import FileSerializer


class TableSerializer(serializers.ModelSerializer):
    file = FileSerializer()

    class Meta:
        model = Table
        fields = ['id', 'name', 'created', 'modified', 'dataset_name', 'data_expiration',
                  'number_of_rows', 'total_logical_bytes', 'reference_name', 'path', 'file']
