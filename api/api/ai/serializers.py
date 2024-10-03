
# Rest Framework
from rest_framework import serializers

class ChatSerializer(serializers.Serializer):
    msg = serializers.CharField()
