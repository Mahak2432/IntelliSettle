"""Test doubles for evidence sources and AI components."""

from __future__ import annotations

from claims_api.domain.models import DocumentExtraction, DocumentUpload, EvidenceItem, Signal
from claims_api.evidence.base import EvidenceCollector
from tests import factories as f


class FixedCollector(EvidenceCollector):
    def __init__(self, name: str, signal: Signal, independent: bool = True, **metrics) -> None:
        self.name = name
        self.label = name
        self.item = f.evidence(name, signal, independent, **metrics)

    async def collect(self, ctx) -> EvidenceItem:
        return self.item


class BrokenCollector(EvidenceCollector):
    def __init__(self, name: str) -> None:
        self.name = name
        self.label = name

    async def collect(self, ctx) -> EvidenceItem:
        raise TimeoutError("upstream timed out")


class BrokenScorer:
    async def score(self, *args):
        raise RuntimeError("model unavailable")


class FixedDocumentReader:
    def __init__(self, **extractions: DocumentExtraction) -> None:
        self.extractions = extractions

    async def read(self, document: DocumentUpload) -> DocumentExtraction:
        return self.extractions.get(document.kind) or f.extraction(document.kind)


def genuine_flood_collectors() -> dict[str, EvidenceCollector]:
    return {
        "weather": FixedCollector("weather", Signal.INCONCLUSIVE, max_24h_mm=35.0),
        "satellite": FixedCollector("satellite", Signal.SUPPORTS, flooded_fraction=0.42),
        "news": FixedCollector("news", Signal.SUPPORTS),
        "photo": FixedCollector("photo", Signal.SUPPORTS, independent=False),
    }


def fake_flood_collectors() -> dict[str, EvidenceCollector]:
    return {
        "weather": FixedCollector("weather", Signal.INCONCLUSIVE, max_24h_mm=0.0),
        "satellite": FixedCollector("satellite", Signal.CONTRADICTS, flooded_fraction=0.0),
        "news": FixedCollector("news", Signal.INCONCLUSIVE),
        "photo": FixedCollector("photo", Signal.INCONCLUSIVE, independent=False),
    }
