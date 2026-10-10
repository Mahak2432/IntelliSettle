from datetime import date, datetime

import pytest

from claims_api.domain.models import ClaimStatus, GeoPoint, Peril, Verdict
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import HeuristicTruthScorer
from claims_api.infra.storage import LocalBlobStore
from claims_api.services.claims import ClaimError, ClaimService, NewDocument, NewPhoto
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.store.claims import InMemoryClaimRepository, InMemoryThresholdStore
from tests import factories as f
from tests import stubs

FILED_AT = datetime(2024, 9, 30, 10, 0, tzinfo=f.IST)


def service(tmp_path, collectors) -> ClaimService:
    reference = ReferenceData(
        farmers=[f.farmer()],
        policies=[f.policy()],
        land_records=[f.land_record()],
        sowing_records=[f.sowing_record()],
    )
    heuristic = HeuristicTruthScorer()
    return ClaimService(
        repo=InMemoryClaimRepository(),
        reference=reference,
        assessor=ClaimAssessor(collectors, heuristic, heuristic, stubs.FixedDocumentReader()),
        blobs=LocalBlobStore(tmp_path),
        thresholds=InMemoryThresholdStore(),
        payouts=SimulatedPayoutRail(),
        clock=lambda: FILED_AT,
    )


async def submit(svc: ClaimService, seed: int = 0):
    near_plot = GeoPoint(lat=f.PLOT_LOCATION.lat + 0.001, lon=f.PLOT_LOCATION.lon)
    taken = datetime(2024, 9, 30, 8, 30, tzinfo=f.IST)
    return await svc.submit(
        farmer_id="F-001",
        policy_no="POL-001",
        peril=Peril.FLOOD,
        loss_date=date(2024, 9, 29),
        description="धान का खेत पानी में डूब गया",
        photos=[NewPhoto(data=f.jpeg(taken, near_plot, seed=seed))],
        documents=[
            NewDocument(kind="land_record", data=f.jpeg(seed=seed + 50)),
            NewDocument(kind="bank_passbook", data=f.jpeg(seed=seed + 90)),
        ],
    )


async def test_genuine_claim_is_fast_approved_and_paid(tmp_path):
    svc = service(tmp_path, stubs.genuine_flood_collectors())
    claim = await svc.assess((await submit(svc)).claim_id)
    assert claim.status == ClaimStatus.READY_FOR_REVIEW
    assert claim.assessment.verdict == Verdict.LOOKS_GENUINE
    assert claim.photos[0].exif_location is not None

    paid = await svc.decide(claim.claim_id, action="approve", fast_lane=True, reason=None, reviewer_id="R1")
    assert paid.status == ClaimStatus.PAID
    assert paid.payout.amount_inr == 24000
    assert paid.payout.reference.startswith("SIM")
    assert [e.status for e in paid.timeline] == [
        "submitted",
        "assessing",
        "ready_for_review",
        "approved",
        "paid",
    ]


async def test_fast_approve_is_refused_unless_claim_looks_genuine(tmp_path):
    svc = service(tmp_path, stubs.fake_flood_collectors())
    claim = await svc.assess((await submit(svc)).claim_id)
    assert claim.assessment.verdict == Verdict.LOOKS_SUSPICIOUS
    with pytest.raises(ClaimError, match="Fast approve"):
        await svc.decide(claim.claim_id, action="approve", fast_lane=True, reason=None, reviewer_id="R1")


async def test_fast_reject_then_one_appeal_with_full_review(tmp_path):
    svc = service(tmp_path, stubs.fake_flood_collectors())
    claim = await svc.assess((await submit(svc)).claim_id)
    rejected = await svc.decide(
        claim.claim_id, action="reject", fast_lane=True, reason=None, reviewer_id="R1"
    )
    assert rejected.status == ClaimStatus.REJECTED

    appealed = await svc.appeal(
        claim.claim_id, "F-001", "Water came from the river, not rain. Please recheck."
    )
    assert appealed.status == ClaimStatus.APPEALED
    with pytest.raises(ClaimError, match="full review"):
        await svc.decide(claim.claim_id, action="reject", fast_lane=True, reason=None, reviewer_id="R2")

    final = await svc.decide(
        claim.claim_id,
        action="reject",
        fast_lane=False,
        reason="Radar clear the day after.",
        reviewer_id="R2",
    )
    assert final.status == ClaimStatus.REJECTED
    with pytest.raises(ClaimError, match="already been appealed"):
        await svc.appeal(claim.claim_id, "F-001", "Please look again at my claim.")


async def test_full_review_requires_a_reason(tmp_path):
    svc = service(tmp_path, stubs.genuine_flood_collectors())
    claim = await svc.assess((await submit(svc)).claim_id)
    with pytest.raises(ClaimError, match="reason"):
        await svc.decide(claim.claim_id, action="reject", fast_lane=False, reason="no", reviewer_id="R1")


async def test_cannot_approve_when_no_trigger_was_met(tmp_path):
    collectors = stubs.genuine_flood_collectors() | {
        "satellite": stubs.FixedCollector("satellite", stubs.Signal.SUPPORTS, flooded_fraction=0.05)
    }
    svc = service(tmp_path, collectors)
    claim = await svc.assess((await submit(svc)).claim_id)
    with pytest.raises(ClaimError, match="No payout trigger"):
        await svc.decide(
            claim.claim_id, action="approve", fast_lane=False, reason="Looks fine to me.", reviewer_id="R1"
        )


async def test_second_claim_with_same_photo_is_flagged(tmp_path):
    svc = service(tmp_path, stubs.genuine_flood_collectors())
    await submit(svc, seed=3)
    second = await svc.assess((await submit(svc, seed=3)).claim_id)
    codes = {c.code: c.status for c in second.assessment.checks}
    assert codes["no_reused_photo"] == "fail"
    assert codes["no_duplicate_claim"] == "fail"
    assert second.assessment.verdict == Verdict.LOOKS_SUSPICIOUS


async def test_farmer_cannot_claim_on_someone_elses_policy(tmp_path):
    svc = service(tmp_path, stubs.genuine_flood_collectors())
    with pytest.raises(ClaimError, match="Policy not found"):
        await svc.submit(
            farmer_id="F-999",
            policy_no="POL-001",
            peril=Peril.FLOOD,
            loss_date=date(2024, 9, 29),
            description="x",
            photos=[NewPhoto(data=f.jpeg())],
        )
