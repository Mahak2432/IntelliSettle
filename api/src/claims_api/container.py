"""Builds the object graph once per process from settings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from claims_api.ai.documents import DocumentReader
from claims_api.ai.gemini import GeminiClient
from claims_api.config import Settings, get_settings
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import GeminiTruthScorer, HeuristicTruthScorer
from claims_api.evidence.base import EvidenceCollector
from claims_api.evidence.news import NewsCollector
from claims_api.evidence.photo import PhotoCollector
from claims_api.evidence.satellite import SatelliteCollector
from claims_api.evidence.weather import WeatherCollector
from claims_api.infra.replay import Recorder
from claims_api.infra.storage import BlobStore, GcsBlobStore, LocalBlobStore
from claims_api.services.alerts import RainAlertService
from claims_api.services.claims import ClaimService
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.services.sessions import InMemorySessionStore, SessionStore
from claims_api.store.claims import (
    FirestoreClaimRepository,
    FirestoreThresholdStore,
    InMemoryClaimRepository,
    InMemoryThresholdStore,
)


@dataclass
class Container:
    settings: Settings
    reference: ReferenceData
    blobs: BlobStore
    claims: ClaimService
    sessions: SessionStore
    gemini: GeminiClient | None
    alerts: RainAlertService | None = None


def build_container(settings: Settings) -> Container:
    recorder = Recorder(settings.external_mode, settings.recordings_dir)
    blobs: BlobStore = (
        GcsBlobStore(settings.storage_bucket)
        if settings.storage_bucket
        else LocalBlobStore(settings.uploads_dir)
    )
    gemini = GeminiClient(settings, recorder)
    collectors: dict[str, EvidenceCollector] = {"weather": WeatherCollector(recorder)}
    heuristic = HeuristicTruthScorer()
    scorer = heuristic
    reader = None
    if settings.ai_enabled or settings.external_mode == "replay":
        collectors |= {
            "satellite": SatelliteCollector(settings, recorder),
            "news": NewsCollector(gemini),
            "photo": PhotoCollector(gemini, blobs),
        }
        scorer = GeminiTruthScorer(gemini)
        reader = DocumentReader(gemini, blobs)

    if settings.storage_backend == "firestore":
        from claims_api.services.sessions import FirestoreSessionStore

        repo = FirestoreClaimRepository(settings.gcp_project)
        thresholds = FirestoreThresholdStore(settings.gcp_project)
        sessions: SessionStore = FirestoreSessionStore(settings.gcp_project)
    else:
        repo, thresholds, sessions = (
            InMemoryClaimRepository(),
            InMemoryThresholdStore(),
            InMemorySessionStore(),
        )

    reference = ReferenceData.load(settings.seed_dir)
    service = ClaimService(
        repo=repo,
        reference=reference,
        assessor=ClaimAssessor(collectors, scorer, heuristic, reader),
        blobs=blobs,
        thresholds=thresholds,
        payouts=SimulatedPayoutRail(),
    )
    return Container(settings, reference, blobs, service, sessions, gemini, RainAlertService(recorder))


@lru_cache
def get_container() -> Container:
    return build_container(get_settings())
