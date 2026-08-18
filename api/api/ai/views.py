"""
AI ViewSet — synchronous for now.
api/api/ai/views.py

NOTE: This was originally designed as async (Celery + Events polling),
but the Event model/EventService job-status tracking was never finished
(no status/payload fields, no detail route, no AI event type). Reverted
to a synchronous response until that's built out properly. See
production readiness doc for details.
"""

from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.ai.exceptions import UnrelatedTopicException
from api.ai.serializers import ChatSerializer
from api.ai.services import ChatAssistant


class AiViewset(viewsets.ViewSet):
    serializer_class = ChatSerializer

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def chat(self, request, *args, **kwargs):
        serializer = ChatSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        msg: str = serializer.validated_data["msg"]
        table = serializer.validated_data["table"]
        context = f"table_id = {table.path}\n" f"bigquery table_schema = {table.schema}"

        try:
            result = ChatAssistant.chat(msg, context)
        except UnrelatedTopicException as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "complete", "explanation": result.explanation, "query": result.query},
            status=status.HTTP_200_OK,
        )
