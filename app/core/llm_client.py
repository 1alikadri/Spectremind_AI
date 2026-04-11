
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import Any

import requests


class LocalLLMError(Exception):
    pass


@dataclass
class LocalLLMClient:
    base_url: str = "http://127.0.0.1:1234/v1"
    model: str = "local-model"
    timeout: int = 120
    chat_completions_path: str = "/chat/completions"

    def _endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.chat_completions_path}"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        try:
            response = requests.post(
                self._endpoint(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LocalLLMError(f"LLM request failed: {exc}") from exc

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            raise LocalLLMError("LLM returned non-JSON response.") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LocalLLMError("LLM response missing expected chat content.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LocalLLMError("LLM response content was empty.")

        return content.strip()
    def _strip_code_fences(self, text: str) -> str:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        return cleaned.strip()

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> dict[str, Any]:
        raw = self.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)
        cleaned = self._strip_code_fences(raw)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LocalLLMError("LLM did not return valid JSON.") from exc

        if not isinstance(data, dict):
            raise LocalLLMError("LLM JSON response must be an object.")

        return data