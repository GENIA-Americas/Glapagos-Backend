"""
AI ViewSet — synchronous by design.
api/api/ai/views.py

DECISION (2026-08-21): this was originally scaffolded as async
(Celery + Events polling), but that job-status system was never
finished (no status/payload fields on Event, no EventService
mark_complete/mark_failed, no detail route, no AI event type).

Rather than build that out under time pressure, we've formally
committed to a synchronous response for now. This is a considered
tradeoff, not a stopgap: revisit if/when request volume or LLM latency
makes blocking a gunicorn worker per chat request a real problem.

The Celery worker (remarkable-endurance) currently has nothing
dispatched to it as a result — see production readiness doc for the
cost/keep-idle decision.
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
