from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from api.notebooks.enums import VERTEX_AI_LOCATIONS


class AcceleratorSerializer(serializers.Serializer):
    zone = serializers.CharField(max_length=30)

    def validate_zone(self, value):
        valid_zones = [loc[0] for loc in VERTEX_AI_LOCATIONS]

        if value not in valid_zones:
            raise serializers.ValidationError(
                _("The zone '{zone}' is not valid").format(zone=value)
            )

        return value