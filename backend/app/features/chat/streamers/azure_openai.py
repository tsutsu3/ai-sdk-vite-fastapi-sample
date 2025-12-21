from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncAzureOpenAI

from app.core.config import AppConfig
from app.features.chat.streamers.base import BaseStreamer
from app.features.title.utils import generate_fallback_title


class AzureOpenAIStreamer(BaseStreamer):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        if not config.azure_openai_endpoint or not config.azure_openai_api_key:
            raise RuntimeError("Azure OpenAI config is missing.")
        self._client = AsyncAzureOpenAI(
            api_key=config.azure_openai_api_key,
            api_version=config.azure_openai_api_version,
            azure_endpoint=config.azure_openai_endpoint,
        )
        self._deployments = config.azure_openai_deployments

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        if not model_id or model_id not in self._deployments:
            raise RuntimeError("Requested model is not available.")
        deployment = self._deployments[model_id]
        stream = await self._client.chat.completions.create(
            model=deployment,
            messages=messages,
            stream=True,
        )
        async for event in stream:
            choice = event.choices[0] if event.choices else None
            delta = choice.delta.content if choice and choice.delta else None
            if delta:
                yield delta

    async def generate_title(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> str:
        if not model_id or model_id not in self._deployments:
            raise RuntimeError("Requested model is not available.")
        prompt = (
            "Summarize the user's request as a short chat title. "
            "Return only the title text, max 60 characters."
        )
        user_text = generate_fallback_title(messages)
        response = await self._client.chat.completions.create(
            model=self._deployments[model_id],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
            max_tokens=40,
        )
        return (response.choices[0].message.content or "").strip()
