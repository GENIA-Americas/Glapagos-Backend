"""Health check views."""

from datetime import datetime, timezone

from channels.layers import get_channel_layer
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

        all_healthy = database_status == "ok" and redis_status == "ok"
        overall = "healthy" if all_healthy else "unhealthy"
        http_status = (
            status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(
            {
                "status": overall,
                "database": database_status,
                "redis": redis_status,
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
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return "error"
            return "ok"
        except Exception:
            return "error"
