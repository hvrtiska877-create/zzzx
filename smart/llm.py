from __future__ import annotations

import json
import os
import urllib.request


class LLMClient:
    """OpenAI-compatible chat client. Works with free providers like OpenRouter free models."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("SMART_API_BASE") or "https://openrouter.ai/api/v1").rstrip("/")
        self.api_key = api_key or os.getenv("SMART_API_KEY")
        self.model = model or os.getenv("SMART_MODEL") or "meta-llama/llama-3.1-8b-instruct:free"
        if not self.api_key:
            raise ValueError("SMART_API_KEY is required")

    def chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SMART/0.1",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
