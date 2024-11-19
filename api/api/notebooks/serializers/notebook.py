from rest_framework import serializers

from api.notebooks.models import Notebook


class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = "__all__"


class StartNotebookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
