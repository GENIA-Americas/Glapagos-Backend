"""
Health check view.
api/api/health/views.py

Response schema:
  {
    "status": "healthy" | "degraded",
    "version": str,
    "timestamp": ISO8601,
    "services": {
      "database": {"status": "ok"|"error", "latency_ms": float, "error": str|None},
      "redis":    {"status": "ok"|"error", "latency_ms": float, "error": str|None},
      "celery":   {"status": "ok"|"error", "workers": int,      "error": str|None},
    }
  }
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import redis
from django.conf import settings
from django.db import connections, DatabaseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

VERSION = getattr(settings, "API_VERSION", "1.0.0")


def _check_database() -> dict:
    t0 = time.monotonic()
    try:
        connections["default"].cursor()
        return {
            "status": "ok",
            "latency_ms": round((time.monotonic() - t0) * 1000, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency_ms": round((time.monotonic() - t0) * 1000, 2),
            "error": str(exc),
        }


def _check_redis() -> dict:
    t0 = time.monotonic()
    try:
        hosts = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"]
        host = hosts[0]
        if isinstance(host, str):
            client = redis.from_url(host)
        else:
            client = redis.Redis(host=host[0], port=host[1])
        client.ping()
        return {
            "status": "ok",
            "latency_ms": round((time.monotonic() - t0) * 1000, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency_ms": round((time.monotonic() - t0) * 1000, 2),
            "error": str(exc),
        }


def _check_celery() -> dict:
    try:
        from celery import current_app
        inspector = current_app.control.inspect(timeout=2)
        stats = inspector.stats() or {}
        workers = len(stats)
        if workers:
            return {"status": "ok", "workers": workers, "error": None}
        return {
            "status": "error",
            "workers": 0,
            "error": "No Celery workers responded to ping",
        }
    except Exception as exc:
        return {"status": "error", "workers": 0, "error": str(exc)}


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        services = {
            "database": _check_database(),
            "redis": _check_redis(),
            "celery": _check_celery(),
        }
        all_ok = all(s["status"] == "ok" for s in services.values())
        return Response(
            {
                "status": "healthy" if all_ok else "degraded",
                "version": VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "services": services,
            },
            status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
