import os
import requests

class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt
        }

        resp = requests.post(f"{self.base_url}/api/generate", json=payload)
        resp.raise_for_status()

        data = resp.json()
        return data.get("response", "")
