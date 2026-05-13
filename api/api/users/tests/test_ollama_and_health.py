"""
Glápagos Backend — Test Suite
tests/test_ollama_client.py + tests/test_health.py

Run with:
    pytest tests/ -v

Covers:
  - OllamaClient.complete()
  - OllamaClient.stream()
  - OllamaClient.health_check()
  - /health/ endpoint (all services healthy, one service down)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import requests


# ===========================================================================
# OllamaClient tests
# ===========================================================================

class TestOllamaClientComplete:
    """Tests for OllamaClient.complete()"""

    def setup_method(self):
        from apps.ai.clients.ollama_client import OllamaClient
        self.client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3",
            timeout=10,
        )

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_complete_returns_response_text(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hola desde Glápagos!", "done": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.complete("Di hola")

        assert result == "Hola desde Glápagos!"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["model"] == "llama3"
        assert call_kwargs[1]["json"]["stream"] is False

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_complete_raises_on_connection_error(self, mock_post):
        from apps.ai.clients.ollama_client import OllamaConnectionError
        mock_post.side_effect = requests.exceptions.ConnectionError("refused")

        with pytest.raises(OllamaConnectionError, match="ollama serve"):
            self.client.complete("test prompt")

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_complete_passes_options_to_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "ok", "done": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.client.complete("test", temperature=0.7, top_p=0.9)

        payload = mock_post.call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.7
        assert payload["options"]["top_p"] == 0.9

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_complete_raises_on_timeout(self, mock_post):
        from apps.ai.clients.ollama_client import OllamaClientError
        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(OllamaClientError, match="timed out"):
            self.client.complete("test")


class TestOllamaClientStream:
    """Tests for OllamaClient.stream()"""

    def setup_method(self):
        from apps.ai.clients.ollama_client import OllamaClient
        self.client = OllamaClient(base_url="http://localhost:11434", model="llama3")

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_stream_yields_tokens(self, mock_post):
        chunks = [
            json.dumps({"response": "Hola", "done": False}).encode(),
            json.dumps({"response": " mundo", "done": False}).encode(),
            json.dumps({"response": "!", "done": True}).encode(),
        ]
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.iter_lines.return_value = chunks
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        tokens = list(self.client.stream("test"))

        assert tokens == ["Hola", " mundo", "!"]

    @patch("apps.ai.clients.ollama_client.requests.Session.post")
    def test_stream_raises_on_connection_error(self, mock_post):
        from apps.ai.clients.ollama_client import OllamaConnectionError
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(OllamaConnectionError):
            list(self.client.stream("test"))


class TestOllamaClientHealthCheck:
    """Tests for OllamaClient.health_check()"""

    def setup_method(self):
        from apps.ai.clients.ollama_client import OllamaClient
        self.client = OllamaClient(base_url="http://localhost:11434", model="llama3")

    @patch("apps.ai.clients.ollama_client.requests.Session.get")
    def test_health_check_model_available(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.health_check()

        assert result["status"] == "ok"
        assert result["model_available"] is True
        assert result["error"] is None

    @patch("apps.ai.clients.ollama_client.requests.Session.get")
    def test_health_check_model_not_pulled(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "mistral:latest"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.health_check()

        assert result["status"] == "ok"
        assert result["model_available"] is False
        assert "ollama pull" in result["error"]

    @patch("apps.ai.clients.ollama_client.requests.Session.get")
    def test_health_check_server_unreachable(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = self.client.health_check()

        assert result["status"] == "error"
        assert "unreachable" in result["error"]


# ===========================================================================
# Health endpoint tests (Django)
# ===========================================================================

class TestHealthEndpoint:
    """Tests for GET /health/"""

    @pytest.fixture
    def client(self, django_test_client):
        return django_test_client

    @patch("api.health.views._check_database")
    @patch("api.health.views._check_redis")
    @patch("api.health.views._check_celery")
    def test_returns_200_when_all_healthy(
        self, mock_celery, mock_redis, mock_db, client
    ):
        mock_db.return_value = {"status": "ok", "latency_ms": 1.2, "error": None}
        mock_redis.return_value = {"status": "ok", "latency_ms": 0.8, "error": None}
        mock_celery.return_value = {"status": "ok", "workers": 2, "error": None}

        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"]["status"] == "ok"
        assert data["services"]["redis"]["status"] == "ok"
        assert data["services"]["celery"]["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data

    @patch("api.health.views._check_database")
    @patch("api.health.views._check_redis")
    @patch("api.health.views._check_celery")
    def test_returns_503_when_database_down(
        self, mock_celery, mock_redis, mock_db, client
    ):
        mock_db.return_value = {
            "status": "error", "latency_ms": 5001.0,
            "error": "could not connect to server"
        }
        mock_redis.return_value = {"status": "ok", "latency_ms": 0.8, "error": None}
        mock_celery.return_value = {"status": "ok", "workers": 1, "error": None}

        response = client.get("/health/")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"]["status"] == "error"

    @patch("api.health.views._check_database")
    @patch("api.health.views._check_redis")
    @patch("api.health.views._check_celery")
    def test_returns_503_when_celery_no_workers(
        self, mock_celery, mock_redis, mock_db, client
    ):
        mock_db.return_value = {"status": "ok", "latency_ms": 1.0, "error": None}
        mock_redis.return_value = {"status": "ok", "latency_ms": 0.5, "error": None}
        mock_celery.return_value = {
            "status": "error", "workers": 0,
            "error": "No Celery workers responded to ping"
        }

        response = client.get("/health/")

        assert response.status_code == 503
        assert response.json()["status"] == "degraded"

    @patch("api.health.views._check_database")
    @patch("api.health.views._check_redis")
    @patch("api.health.views._check_celery")
    def test_response_schema_is_complete(
        self, mock_celery, mock_redis, mock_db, client
    ):
        """Ensure every field in the documented schema is present."""
        mock_db.return_value = {"status": "ok", "latency_ms": 1.0, "error": None}
        mock_redis.return_value = {"status": "ok", "latency_ms": 0.5, "error": None}
        mock_celery.return_value = {"status": "ok", "workers": 1, "error": None}

        data = client.get("/health/").json()

        assert set(data.keys()) >= {"status", "version", "timestamp", "services"}
        assert set(data["services"].keys()) == {"database", "redis", "celery"}
