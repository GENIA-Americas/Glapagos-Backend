from django.test import TestCase
from django.conf import settings
from apps.ai.clients.ollama import OllamaClient


class TestOllamaClient(TestCase):
    def setUp(self):
        # 强制设置环境变量，避免 CI 报错
        settings.AI_PROVIDER = "ollama"
        settings.OLLAMA_BASE_URL = "http://localhost:11434"
        settings.OLLAMA_MODEL = "llama3"

        self.client = OllamaClient()

    def test_client_initializes(self):
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.base_url, "http://localhost:11434")
        self.assertEqual(self.client.model, "llama3")

    def test_build_payload(self):
        payload = self.client._build_payload("hello")

        self.assertIn("model", payload)
        self.assertIn("prompt", payload)
        self.assertEqual(payload["model"], "llama3")
        self.assertEqual(payload["prompt"], "hello")

    def test_generate_does_not_crash_on_request_error(self):
        try:
            self.client.generate("test")
        except Exception as e:
            self.assertNotIsInstance(e, AttributeError)
            self.assertNotIsInstance(e, KeyError)
