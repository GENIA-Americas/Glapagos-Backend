"""
AI ViewSet — async-first design.
api/api/ai/views.py

The chat endpoint no longer blocks on inference.
It creates an Event, dispatches the Celery task, and returns the
job_id immediately (HTTP 202). The client tracks progress via WebSocket
or polls /api/v1/events/<id>/.
"""
from __future__ import annotations

import uuid

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.ai.serializers import ChatSerializer
from api.ai.tasks import run_chat


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
        context = (
            f"table_id = {table.path}\n"
            f"bigquery table_schema = {table.schema}"
        )

        event_id = str(uuid.uuid4())

        run_chat.delay(msg=msg, context=context, event_id=event_id)

        return Response(
            {"job_id": event_id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )
