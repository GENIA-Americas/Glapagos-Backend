"""Health check views."""
import redis
from django.conf import settings

from datetime import datetime, timezone

from django.db import DatabaseError
from django.db import connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Check the health of connected services."""

    permission_classes = [AllowAny]

    def get(self, request):
        database_status = self._check_database()
        redis_status = self._check_redis()
        celery_status = self._check_celery()

        all_healthy = (
            database_status == "ok"
            and redis_status == "ok"
            and celery_status == "ok"
        )
        overall = "healthy" if all_healthy else "unhealthy"
        http_status = (
            status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(
            {
                "status": overall,
                "database": database_status,
                "redis": redis_status,
                "celery": celery_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            status=http_status,
        )

    def _check_database(self):
        try:
            connections["default"].cursor()
            return "ok"
        except DatabaseError:
            return "error"

    def _check_redis(self):
        try:

            hosts = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"]
            host = hosts[0]

            if isinstance(host, str):
                client = redis.from_url(host)
            else:
                client = redis.Redis(host=host[0], port=host[1])

            client.ping()
            return "ok"
        except Exception:
            return "error"

    def _check_celery(self):
        try:
            from celery import current_app

            inspector = current_app.control.inspect(timeout=2)
            stats = inspector.stats()
            if stats:
                return "ok"
            return "error"
        except Exception:
            return "error"
