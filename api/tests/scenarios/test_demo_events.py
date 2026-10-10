"""The demo, as tests: three real Bihar disasters and one fake claim.

Every run replays saved responses from the real services, so these always run
on real rainfall, radar and news data without network access. Refresh them with
`uv run pytest tests/scenarios --record` (Open-Meteo needs no key; Earth Engine
and Gemini need GCP credentials, see docs/SETUP_GCP.md).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from claims_api.ai.documents import DocumentReader
from claims_api.ai.gemini import GeminiClient
from claims_api.config import REPO_ROOT, Settings
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import Claim
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import GeminiTruthScorer, HeuristicTruthScorer
from claims_api.evidence.news import NewsCollector
from claims_api.evidence.photo import PhotoCollector
from claims_api.evidence.satellite import SatelliteCollector
from claims_api.evidence.weather import WeatherCollector
from claims_api.infra.replay import MissingRecording, Recorder
from claims_api.infra.storage import LocalBlobStore
from claims_api.services.claims import ClaimService, NewDocument, NewPhoto
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.store.claims import InMemoryClaimRepository, InMemoryThresholdStore

SEED = REPO_ROOT / "data" / "seed"
DEMO_ASSETS = REPO_ROOT / "web" / "public" / "demo"
RECORDINGS = Path(__file__).resolve().parents[1] / "recordings"
SCENARIOS = json.loads((SEED / "scenarios.json").read_text(encoding="utf-8"))
REFERENCE = ReferenceData.load(SEED)

pytestmark = pytest.mark.scenario


class TrackingRecorder(Recorder):
    """Remembers replay misses, because the pipeline turns source failures into 'unavailable'."""

    def __init__(self, mode, directory):
        super().__init__(mode, directory)
        self.missing: list[str] = []

    async def call(self, namespace, request, fetch):
        try:
            return await super().call(namespace, request, fetch)
        except MissingRecording:
            self.missing.append(namespace)
            raise


@pytest.fixture
def recorder(request) -> TrackingRecorder:
    mode = "record" if request.config.getoption("--record") else "replay"
    return TrackingRecorder(mode, RECORDINGS)


def context_for(scenario: dict) -> ClaimContext:
    policy = REFERENCE.policy(scenario["policy_no"])
    farmer = REFERENCE.farmer(scenario["farmer_id"])
    claim = Claim(
        claim_id=f"SCN-{scenario['id']}",
        policy_no=policy.policy_no,
        farmer_id=farmer.farmer_id,
        product_code=policy.product_code,
        peril=scenario["peril"],
        loss_date=date.fromisoformat(scenario["loss_date"]),
        submitted_at=datetime.fromisoformat(scenario["filed_at"]),
        description=scenario["description"],
    )
    return ClaimContext(
        claim=claim,
        policy=policy,
        farmer=farmer,
        land_record=REFERENCE.land_record(policy.plot.village, policy.plot.khasra_no),
        sowing_record=REFERENCE.sowing_record(farmer.farmer_id, policy.plot.khasra_no, policy.season),
    )


def by_id(scenario: dict) -> str:
    return scenario["id"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=by_id)
async def test_rainfall_at_the_plot_matches_the_real_event(scenario, recorder):
    ctx = context_for(scenario)
    item = await WeatherCollector(recorder).collect(ctx)
    m, expect = item.metrics, scenario["weather"]

    if "max_24h_mm_at_least" in expect:
        assert m["max_24h_mm"] >= expect["max_24h_mm_at_least"]
    if "max_24h_mm_below" in expect:
        assert m["max_24h_mm"] < expect["max_24h_mm_below"]
    if "flood_day_rain_below" in expect:
        assert m["daily_mm"][scenario["loss_date"]] < expect["flood_day_rain_below"]
    if "max_hourly_mm_at_least" in expect:
        assert m["max_hourly_mm"] >= expect["max_hourly_mm_at_least"]
    if "window_total_mm_below" in expect:
        assert m["window_total_mm"] < expect["window_total_mm_below"]


def demo_files(farmer_id: str) -> tuple[list[Path], dict[str, Path]]:
    folder = DEMO_ASSETS / farmer_id
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        return [], {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    photos = [folder / p for p in manifest.get("photos", [])]
    docs = {k: folder / manifest[k] for k in ("land_record", "bank_passbook") if manifest.get(k)}
    return photos, docs


@pytest.mark.parametrize("scenario", SCENARIOS, ids=by_id)
async def test_full_ai_assessment_reaches_the_expected_verdict(scenario, recorder, tmp_path):
    photos, docs = demo_files(scenario["farmer_id"])
    if not photos:
        pytest.skip(f"Demo photos for {scenario['farmer_id']} are not in web/public/demo yet.")

    settings = Settings(_env_file=None) if recorder.mode == "replay" else Settings()
    gemini = GeminiClient(settings, recorder)
    blobs = LocalBlobStore(tmp_path)
    heuristic = HeuristicTruthScorer()
    filed_at = datetime.fromisoformat(scenario["filed_at"])
    service = ClaimService(
        repo=InMemoryClaimRepository(),
        reference=REFERENCE,
        assessor=ClaimAssessor(
            {
                "weather": WeatherCollector(recorder),
                "satellite": SatelliteCollector(settings, recorder),
                "news": NewsCollector(gemini),
                "photo": PhotoCollector(gemini, blobs),
            },
            GeminiTruthScorer(gemini),
            heuristic,
            DocumentReader(gemini, blobs),
        ),
        blobs=blobs,
        thresholds=InMemoryThresholdStore(),
        payouts=SimulatedPayoutRail(),
        clock=lambda: filed_at,
    )
    claim = await service.submit(
        farmer_id=scenario["farmer_id"],
        policy_no=scenario["policy_no"],
        peril=scenario["peril"],
        loss_date=date.fromisoformat(scenario["loss_date"]),
        description=scenario["description"],
        photos=[NewPhoto(data=p.read_bytes()) for p in photos],
        documents=[NewDocument(kind=k, data=p.read_bytes()) for k, p in docs.items()],
    )
    assessed = await service.assess(claim.claim_id)

    if recorder.missing:
        pytest.skip(
            f"Missing saved responses for {sorted(set(recorder.missing))}. "
            "Run `uv run pytest tests/scenarios --record` with GCP credentials once."
        )
    a = assessed.assessment
    summary = {c.code: c.status for c in a.checks} | {e.source: e.signal for e in a.evidence}
    assert a.verdict in scenario["expected_verdicts"], f"score={a.truth.score} {summary} {a.truth.red_flags}"
    assert not a.truth.fallback
