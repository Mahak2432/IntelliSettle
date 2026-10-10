"""Where uploaded photos and documents live: local disk in dev, Cloud Storage in the cloud."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    async def put(self, path: str, data: bytes, content_type: str) -> None: ...
    async def get(self, path: str) -> bytes: ...


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root.resolve()):
            raise ValueError(f"Path escapes storage root: {path}")
        return target

    async def put(self, path: str, data: bytes, content_type: str) -> None:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, data)

    async def get(self, path: str) -> bytes:
        return await asyncio.to_thread(self._resolve(path).read_bytes)


class GcsBlobStore:
    def __init__(self, bucket_name: str) -> None:
        from google.cloud import storage

        self.bucket = storage.Client().bucket(bucket_name)

    async def put(self, path: str, data: bytes, content_type: str) -> None:
        blob = self.bucket.blob(path)
        await asyncio.to_thread(blob.upload_from_string, data, content_type=content_type)

    async def get(self, path: str) -> bytes:
        return await asyncio.to_thread(self.bucket.blob(path).download_as_bytes)
