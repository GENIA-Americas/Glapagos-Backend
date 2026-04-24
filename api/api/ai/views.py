import logging

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import status

from api.ai.serializers import ChatSerializer
from api.ai.services import ChatAssistant

logger = logging.getLogger(__name__)


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
        table = serializer.validated_data.get("table")
        history = serializer.validated_data.get("history", [])

        context = (
            f"table_id = {table.path}\n"
            f"bigquery table_schema = {table.schema}"
        )

        res = ChatAssistant.chat(msg, context, history=history)

        return Response(
            {"message": res.model_dump()},
            status=status.HTTP_200_OK,
        )
