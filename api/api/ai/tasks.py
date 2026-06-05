"""
Celery tasks for async AI inference.
api/api/ai/tasks.py

Views must NOT call providers directly — they dispatch here and return
a job_id immediately. The client polls /events/ or uses the WebSocket
consumer for the result.

Retry policy:
  - 3 attempts with exponential backoff (10s, 20s, 40s).
  - Hard time limit: 5 minutes per task.
  - Soft limit warning at 4 minutes.
"""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 10  # seconds; doubles on each retry


@shared_task(
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    time_limit=300,
    soft_time_limit=240,
    name="ai.run_chat",
)
def run_chat(self, msg: str, context: str, event_id: str) -> dict:
    """
    Executes AI inference off the request cycle.

    Args:
        msg:      The user's natural language question.
        context:  BigQuery table path + schema string.
        event_id: The Event pk to update with the result.

    Returns:
        dict with keys 'explanation' and 'query' on success.
    """
    from api.ai.services import ChatAssistant
    from api.events.service.event_service import EventService

    try:
        result = ChatAssistant.chat(msg, context)
        EventService.mark_complete(event_id, payload=result.__dict__)
        return result.__dict__
    except Exception as exc:
        logger.exception("run_chat failed (attempt %d): %s", self.request.retries + 1, exc)
        EventService.mark_failed(event_id, reason=str(exc))
        raise self.retry(exc=exc, countdown=_RETRY_BACKOFF * (2 ** self.request.retries))
