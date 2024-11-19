from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.datasets.models.table import Table


class PrivateDataAccess (serializers.Serializer):
    table = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.filter(public=False, mounted=True))
    reason = serializers.CharField()
    share_data = serializers.BooleanField(default=False)
    pay_for_access = serializers.BooleanField(default=False)
