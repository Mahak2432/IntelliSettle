from datetime import date, datetime

from claims_api.domain.time import IST
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import HeuristicTruthScorer
from claims_api.infra.storage import LocalBlobStore
from claims_api.services.alerts import categorise
from claims_api.services.claims import ClaimService
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.store.claims import InMemoryClaimRepository, InMemoryThresholdStore
from tests import factories as f


def test_imd_rain_categories():
    assert categorise(64.4) is None
    assert categorise(64.5)[0] == "heavy rain"
    assert categorise(130)[0] == "very heavy rain"
    assert categorise(250)[1] == "अत्यंत भारी बारिश"


def test_demo_farmers_live_on_their_demo_date(tmp_path):
    demo = f.farmer(farmer_id="F-DEMO", demo_today=date(2024, 9, 30))
    reference = ReferenceData([f.farmer(), demo], [], [], [])
    heuristic = HeuristicTruthScorer()
    svc = ClaimService(
        repo=InMemoryClaimRepository(),
        reference=reference,
        assessor=ClaimAssessor({}, heuristic, heuristic),
        blobs=LocalBlobStore(tmp_path),
        thresholds=InMemoryThresholdStore(),
        payouts=SimulatedPayoutRail(),
        clock=lambda: datetime(2026, 10, 12, 15, 45, tzinfo=IST),
    )
    shifted = svc.now_for("F-DEMO")
    assert shifted.date() == date(2024, 9, 30)
    assert (shifted.hour, shifted.minute) == (15, 45)
    assert svc.now_for("F-001").date() == date(2026, 10, 12)
