import re
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.notebooks.models import Notebook
from api.utils.basics import generate_random_string


class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = "__all__"

    def validate_name(self, value):
        """
        Validate and correct the notebook name to meet Google Cloud's requirements.
        """
        value = f"{value}-{generate_random_string(5)}"
        value = value.lower()

        value = re.sub(r'[^a-z0-9-]', '-', value)

        if not value[0].isalpha():
            value = f'a{value}'

        value = value[:58].rstrip('-')

        if not re.match(r'^[a-z][a-z0-9-]{0,57}$', value):
            raise serializers.ValidationError(_("Invalid notebook name after normalization."))

        return value


class StartNotebookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
