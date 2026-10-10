"""Thin wrapper around the Google Gen AI SDK.

Runs on Vertex AI through the service account on Cloud Run (no API key), or on
an AI Studio key for local experiments. Every call goes through the Recorder so
tests can replay real model responses.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from claims_api.config import Settings
from claims_api.infra.replay import Recorder


class AIUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ImageInput:
    data: bytes
    mime_type: str = "image/jpeg"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


class GeminiClient:
    def __init__(self, settings: Settings, recorder: Recorder) -> None:
        self.settings = settings
        self.recorder = recorder
        self._client: genai.Client | None = None

    @property
    def model(self) -> str:
        return self.settings.gemini_model

    def _sdk(self) -> genai.Client:
        if self._client is None:
            if self.settings.gemini_api_key:
                self._client = genai.Client(api_key=self.settings.gemini_api_key)
            elif self.settings.gcp_project:
                self._client = genai.Client(
                    vertexai=True,
                    project=self.settings.gcp_project,
                    location=self.settings.vertex_location,
                )
            else:
                raise AIUnavailable("Set GCP_PROJECT (Vertex AI) or GEMINI_API_KEY to enable Gemini.")
        return self._client

    async def generate_json(
        self,
        *,
        namespace: str,
        system: str,
        prompt: str,
        schema: type[BaseModel],
        images: list[ImageInput] | None = None,
        google_search: bool = False,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Return {"data": <schema-shaped dict>, "sources": [{"title", "url"}]}."""
        images = images or []
        model = model or self.model
        request = {
            "model": model,
            "system": system,
            "prompt": prompt,
            "schema": schema.__name__,
            "images": [img.digest for img in images],
            "google_search": google_search,
        }

        async def fetch() -> dict[str, Any]:
            contents: list[Any] = [types.Part.from_bytes(data=i.data, mime_type=i.mime_type) for i in images]
            contents.append(prompt)
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=0,
                response_mime_type="application/json",
                response_schema=schema,
                tools=[types.Tool(google_search=types.GoogleSearch())] if google_search else None,
            )
            response = await self._sdk().aio.models.generate_content(
                model=model, contents=contents, config=config
            )
            if not response.text:
                raise AIUnavailable(f"Empty response from {model}")
            return {"data": json.loads(response.text), "sources": _grounding_sources(response)}

        return await self.recorder.call(namespace, request, fetch)


def _grounding_sources(response: types.GenerateContentResponse) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for candidate in response.candidates or []:
        metadata = candidate.grounding_metadata
        for chunk in (metadata.grounding_chunks or []) if metadata else []:
            if chunk.web and chunk.web.uri:
                sources.append({"title": chunk.web.title or chunk.web.uri, "url": chunk.web.uri})
    return sources
