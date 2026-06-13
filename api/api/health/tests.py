"""Health check tests."""

from datetime import datetime
from unittest.mock import patch, MagicMock

from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTestCase(APITestCase):

    def setUp(self):
        self.url = f"/{settings.API_URI}/health/"

    def _mock_all(self, db="ok", redis="ok", celery="ok"):
        db_result = {"status": db, "latency_ms": 1.0, "error": None}
        redis_result = {"status": redis, "latency_ms": 0.5, "error": None}
        celery_result = {"status": celery, "workers": 1 if celery == "ok" else 0, "error": None}
        return (
            patch("api.health.views._check_database", return_value=db_result),
            patch("api.health.views._check_redis", return_value=redis_result),
            patch("api.health.views._check_celery", return_value=celery_result),
        )

    def test_all_healthy_returns_200(self):
        p1, p2, p3 = self._mock_all()
        with p1, p2, p3:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertIn("timestamp", response.data)
        self.assertIn("services", response.data)

    def test_database_down_returns_503(self):
        p1, p2, p3 = self._mock_all(db="error")
        with p1, p2, p3:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["services"]["database"]["status"], "error")

    def test_redis_down_returns_503(self):
        p1, p2, p3 = self._mock_all(redis="error")
        with p1, p2, p3:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["services"]["redis"]["status"], "error")

    def test_celery_down_returns_503(self):
        p1, p2, p3 = self._mock_all(celery="error")
        with p1, p2, p3:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["services"]["celery"]["status"], "error")

    def test_all_down_returns_503(self):
        p1, p2, p3 = self._mock_all(db="error", redis="error", celery="error")
        with p1, p2, p3:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "degraded")

    def test_timestamp_is_iso_format(self):
        p1, p2, p3 = self._mock_all()
        with p1, p2, p3:
            response = self.client.get(self.url)
        try:
            datetime.fromisoformat(response.data["timestamp"])
        except (ValueError, KeyError):
            self.fail("timestamp is not a valid ISO 8601 string")

    def test_response_schema_is_complete(self):
        p1, p2, p3 = self._mock_all()
        with p1, p2, p3:
            response = self.client.get(self.url)
        data = response.data
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("services", data)
        self.assertEqual(set(data["services"].keys()), {"database", "redis", "celery"})


class RedisHealthCheckUnitTestCase(APITestCase):

    def test_url_string_host_ping_succeeds_returns_ok(self):
        from api.health.views import _check_redis
        with patch("api.health.views.settings") as mock_settings,              patch("api.health.views.redis") as mock_redis:
            mock_settings.CHANNEL_LAYERS = {
                "default": {"CONFIG": {"hosts": ["redis://localhost:6379"]}}
            }
            mock_redis.from_url.return_value.ping.return_value = True
            result = _check_redis()
        self.assertEqual(result["status"], "ok")

    def test_tuple_host_ping_succeeds_returns_ok(self):
        from api.health.views import _check_redis
        with patch("api.health.views.settings") as mock_settings,              patch("api.health.views.redis") as mock_redis:
            mock_settings.CHANNEL_LAYERS = {
                "default": {"CONFIG": {"hosts": [("redis-host", 6379)]}}
            }
            mock_redis.Redis.return_value.ping.return_value = True
            result = _check_redis()
        self.assertEqual(result["status"], "ok")

    def test_ping_raises_exception_returns_error(self):
        from api.health.views import _check_redis
        with patch("api.health.views.settings") as mock_settings,              patch("api.health.views.redis") as mock_redis:
            mock_settings.CHANNEL_LAYERS = {
                "default": {"CONFIG": {"hosts": ["redis://localhost:6379"]}}
            }
            mock_redis.from_url.return_value.ping.side_effect = Exception("refused")
            result = _check_redis()
        self.assertEqual(result["status"], "error")
