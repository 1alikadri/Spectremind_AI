import requests


class LocalLLMClient:
    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1/chat/completions", model: str = "local-model"):
        self.base_url = base_url
        self.model = model

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        response = requests.post(self.base_url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]