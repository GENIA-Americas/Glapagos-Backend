"""
Glápagos Platform — Health Check Endpoint
api/health/views.py

GET /health/
Returns 200 with a JSON payload when all services are healthy.
Returns 503 when any critical service is degraded.

Services checked:
  - database    (Django ORM connection)
  - redis       (via django-redis / direct connection)
  - celery      (worker ping via Celery inspect)

Response schema:
  {
    "status": "healthy" | "degraded",
    "version": "<APP_VERSION env var>",
    "timestamp": "<ISO-8601>",
    "services": {
      "database": { "status": "ok" | "error", "latency_ms": float, "error": str | null },
      "redis":    { "status": "ok" | "error", "latency_ms": float, "error": str | null },
      "celery":   { "status": "ok" | "error", "workers":    int,   "error": str | null }
    }
  }
"""

from __future__ import annotations

import os
import time
import logging
from datetime import datetime, timezone
from typing import Any

from django.db import connections, OperationalError
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "unknown")
HEALTH_CELERY_TIMEOUT = float(os.environ.get("HEALTH_CELERY_TIMEOUT", "2.0"))
HEALTH_REDIS_TIMEOUT = float(os.environ.get("HEALTH_REDIS_TIMEOUT", "2.0"))


# ---------------------------------------------------------------------------
# Individual service checks
# ---------------------------------------------------------------------------

def _check_database() -> dict[str, Any]:
    start = time.perf_counter()
    try:
        conn = connections["default"]
        conn.ensure_connection()
        # Lightweight query to confirm round-trip
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "ok", "latency_ms": latency, "error": None}
    except OperationalError as exc:
        latency = round((time.perf_counter() - start) * 1000, 2)
        logger.warning("Health check — database error: %s", exc)
        return {"status": "error", "latency_ms": latency, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        latency = round((time.perf_counter() - start) * 1000, 2)
        logger.exception("Health check — unexpected database error")
        return {"status": "error", "latency_ms": latency, "error": str(exc)}


def _check_redis() -> dict[str, Any]:
    start = time.perf_counter()
    try:
        # Prefer django-redis cache if configured, fall back to raw redis-py
        try:
            from django.core.cache import cache
            cache.set("_glapagos_health", "ok", timeout=5)
            val = cache.get("_glapagos_health")
            if val != "ok":
                raise ValueError("Redis round-trip value mismatch")
        except Exception:
            import redis as _redis  # type: ignore[import]
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            client = _redis.from_url(redis_url, socket_timeout=HEALTH_REDIS_TIMEOUT)
            client.ping()

        latency = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "ok", "latency_ms": latency, "error": None}
    except Exception as exc:  # noqa: BLE001
        latency = round((time.perf_counter() - start) * 1000, 2)
        logger.warning("Health check — Redis error: %s", exc)
        return {"status": "error", "latency_ms": latency, "error": str(exc)}


def _check_celery() -> dict[str, Any]:
    try:
        from celery import current_app  # type: ignore[import]
        inspector = current_app.control.inspect(timeout=HEALTH_CELERY_TIMEOUT)
        ping_response = inspector.ping() or {}
        worker_count = len(ping_response)
        if worker_count == 0:
            return {
                "status": "error",
                "workers": 0,
                "error": "No Celery workers responded to ping",
            }
        return {"status": "ok", "workers": worker_count, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Health check — Celery error: %s", exc)
        return {"status": "error", "workers": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class HealthCheckView(View):
    """
    Endpoint: GET /health/

    Returns HTTP 200 when all services are healthy, HTTP 503 otherwise.
    Safe to call unauthenticated — authentication middleware should
    be exempt for this path (configure in settings.py or urls.py).
    """

    http_method_names = ["get", "head"]

    def get(self, request, *args, **kwargs):
        services = {
            "database": _check_database(),
            "redis": _check_redis(),
            "celery": _check_celery(),
        }

        all_healthy = all(s["status"] == "ok" for s in services.values())

        payload = {
            "status": "healthy" if all_healthy else "degraded",
            "version": APP_VERSION,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "services": services,
        }

        http_status = 200 if all_healthy else 503
        return JsonResponse(payload, status=http_status)


# ---------------------------------------------------------------------------
# URL registration helper (add to your urls.py)
# ---------------------------------------------------------------------------
#
# from api.health.views import HealthCheckView
#
# urlpatterns = [
#     ...
#     path("health/", HealthCheckView.as_view(), name="health-check"),
# ]
#
# To exclude from authentication middleware in settings.py:
#   LOGIN_EXEMPT_URLS = [r"^health/$"]
