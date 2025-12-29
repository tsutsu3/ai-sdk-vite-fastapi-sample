import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import AppConfig
from app.features.chat.streamers.base import BaseStreamer
from app.features.messages.models import MessageRecord
from app.features.run.models import OpenAIMessage
from app.features.title.utils import generate_fallback_title


class OllamaStreamer(BaseStreamer):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._base_url = config.ollama_base_url.rstrip("/")

    async def stream_chat(
        self,
        messages: list[OpenAIMessage],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        if not model_id:
            raise RuntimeError("Requested model is not available.")
        url = f"{self._base_url}/api/chat"
        messages_payload = [
            message.model_dump(by_alias=True, exclude_none=True) for message in messages
        ]
        payload = {
            "model": model_id,
            "messages": messages_payload,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if event.get("done"):
                            break
                        message = event.get("message", {})
                        content = message.get("content") if isinstance(message, dict) else None
                        if content:
                            yield str(content)
        except httpx.HTTPError as exc:
            raise RuntimeError("Failed to reach Ollama server.") from exc

    async def generate_title(
        self,
        messages: list[MessageRecord],
        model_id: str | None,
    ) -> str:
        if not model_id:
            raise RuntimeError("Requested model is not available.")
        prompt = (
            "Summarize the user's request as a short chat title. "
            "Return only the title text, max 60 characters."
        )
        user_text = generate_fallback_title(messages)
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return (data.get("message", {}).get("content") or "").strip()
