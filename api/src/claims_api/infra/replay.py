"""Record and replay calls to external services.

Every call to a weather API, Earth Engine or Gemini goes through `Recorder.call`.
In tests we replay saved responses, so the demo scenarios run on real data
every time without network access, cost or flakiness. Running the tests with
`--record` refreshes the saved responses from the live services.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Mode = Literal["live", "record", "replay"]


class MissingRecording(LookupError):
    def __init__(self, path: Path, request: dict[str, Any]) -> None:
        super().__init__(
            f"No saved response at {path}. Run the tests with --record to capture it. Request: {request}"
        )
        self.path = path


def request_key(request: dict[str, Any]) -> str:
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:20]


class Recorder:
    def __init__(self, mode: Mode, directory: Path) -> None:
        self.mode = mode
        self.directory = directory

    def path_for(self, namespace: str, request: dict[str, Any]) -> Path:
        return self.directory / namespace / f"{request_key(request)}.json"

    async def call(self, namespace: str, request: dict[str, Any], fetch: Callable[[], Awaitable[Any]]) -> Any:
        path = self.path_for(namespace, request)
        if self.mode == "replay":
            if not path.exists():
                raise MissingRecording(path, request)
            return json.loads(path.read_text(encoding="utf-8"))["response"]

        response = await fetch()
        if self.mode == "record":
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "request": request,
                "recorded_at": datetime.now(UTC).isoformat(),
                "response": response,
            }
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return response
