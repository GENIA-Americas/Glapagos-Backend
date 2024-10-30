# Rest framework
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import status

# Models
from api.ai.serializers import ChatSerializer
from api.datasets.models import Table

# Permissions
from api.ai.services import ChatAssistant

class AiViewset(viewsets.ViewSet):
    serializer_class = ChatSerializer 

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def chat(self, request, *args, **kwargs):
        serializer = ChatSerializer(
            data=request.data, context=dict(request=request)
        )
        serializer.is_valid(raise_exception=True)

        msg = serializer.validated_data.get("msg", "")
        table = serializer.validated_data.get("table", "")
        context = f"table_id = {table.path} \nbigquery table_schema = {table.schema}"
        res = ChatAssistant.chat(msg, context)

        return Response(dict(message=res.__dict__), status=status.HTTP_200_OK)

