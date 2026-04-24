from rest_framework import serializers
from api.datasets.models import Table


class ChatSerializer(serializers.Serializer):
    msg = serializers.CharField(max_length=2000)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())
    # Optional conversation history for multi-turn support
    history = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=list,
        max_length=20,
    )

    def validate_history(self, value):
        for entry in value:
            if "role" not in entry or "content" not in entry:
                raise serializers.ValidationError(
                    "Each history entry must have 'role' and 'content' keys."
                )
            if entry["role"] not in ("user", "assistant"):
                raise serializers.ValidationError(
                    "History roles must be 'user' or 'assistant'."
                )
        return value
