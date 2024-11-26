
from django.db.models import Q
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from api.datasets.models.table import Table
from api.datasets.services import BigQueryService


class ChatSerializer(serializers.Serializer):
    msg = serializers.CharField(allow_blank=False)
    table = serializers.CharField(allow_blank=False)

    def validate_table(self, value):
        user = self.context["request"].user
        table = Table.objects.filter(
            Q(file__owner=user) | Q(public=True),
            name=value
        ).first()

        if not table:
            raise serializers.ValidationError(_("Table name was not found"))

        bigquery_service = BigQueryService(user=None)
        table.update_schema(bigquery_service)

        return table 
