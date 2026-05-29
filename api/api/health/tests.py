"""Health check tests."""

from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTestCase(APITestCase):
    """Test the health check endpoint."""

    def setUp(self):
        self.url = f"/{settings.API_URI}/health/"

    def test_all_healthy_returns_200(self):
        """Should return 200 and healthy status when all services are ok."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="ok"
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "ok")
        self.assertIn("timestamp", response.data)

    def test_database_down_returns_503(self):
        """Should return 503 when database is down."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="error"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="ok"
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
        self.assertEqual(response.data["database"], "error")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "ok")

    def test_redis_down_returns_503(self):
        """Should return 503 when Redis is down."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="error"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="ok"
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["redis"], "error")
        self.assertEqual(response.data["celery"], "ok")

    def test_celery_down_returns_503(self):
        """Should return 503 when Celery is down."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="error"
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["redis"], "ok")
        self.assertEqual(response.data["celery"], "error")

    def test_all_down_returns_503(self):
        """Should return 503 when all services are down."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="error"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="error"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="error"
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
        self.assertEqual(response.data["database"], "error")
        self.assertEqual(response.data["redis"], "error")
        self.assertEqual(response.data["celery"], "error")

    def test_timestamp_is_iso_format(self):
        """The timestamp field should be an ISO 8601 datetime string."""
        with patch(
            "api.health.views.HealthView._check_database", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_redis", return_value="ok"
        ), patch(
            "api.health.views.HealthView._check_celery", return_value="ok"
        ):
            response = self.client.get(self.url)

        try:
            datetime.fromisoformat(response.data["timestamp"])
        except (ValueError, KeyError):
            self.fail("timestamp is not a valid ISO 8601 string")
