from claims_api.domain.models import ReviewThresholds, Signal, Verdict
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import HeuristicTruthScorer
from claims_api.products.crop import CropParametricProduct
from tests import factories as f
from tests import stubs

product = CropParametricProduct()
thresholds = ReviewThresholds()


def assessor(collectors, scorer=None, reader=None) -> ClaimAssessor:
    heuristic = HeuristicTruthScorer()
    return ClaimAssessor(collectors, scorer or heuristic, heuristic, reader)


async def test_corroborated_flood_looks_genuine_with_radar_payout():
    _, a = await assessor(stubs.genuine_flood_collectors()).assess(f.context(), product, thresholds)
    assert a.verdict == Verdict.LOOKS_GENUINE
    assert a.truth.score >= 80
    assert a.payout_quote.payout_percent == 50
    assert [e.source for e in a.evidence] == ["weather", "satellite", "news", "photo"]


async def test_flood_contradicted_by_radar_looks_suspicious():
    _, a = await assessor(stubs.fake_flood_collectors()).assess(f.context(), product, thresholds)
    assert a.verdict == Verdict.LOOKS_SUSPICIOUS
    assert a.truth.score <= 30


async def test_failing_source_is_marked_unavailable_and_pipeline_continues():
    collectors = stubs.genuine_flood_collectors() | {"news": stubs.BrokenCollector("news")}
    _, a = await assessor(collectors).assess(f.context(), product, thresholds)
    news = next(e for e in a.evidence if e.source == "news")
    assert news.signal == Signal.UNAVAILABLE
    assert "TimeoutError" in news.summary


async def test_ai_outage_falls_back_to_heuristic_and_blocks_fast_approve():
    _, a = await assessor(stubs.genuine_flood_collectors(), scorer=stubs.BrokenScorer()).assess(
        f.context(), product, thresholds
    )
    assert a.truth.fallback is True
    assert a.verdict == Verdict.NEEDS_REVIEW


async def test_unread_documents_are_read_before_checks_run():
    unread = [d.model_copy(update={"extraction": None}) for d in f.documents()]
    ctx = f.context(claim=f.claim(documents=unread))
    claim, a = await assessor(stubs.genuine_flood_collectors(), reader=stubs.FixedDocumentReader()).assess(
        ctx, product, thresholds
    )
    assert all(d.extraction is not None for d in claim.documents)
    assert next(c for c in a.checks if c.code == "documents_match_records").status == "pass"


async def test_hailstorm_plan_skips_satellite():
    ctx = f.context(claim=f.claim(peril="hailstorm"))
    _, a = await assessor(stubs.genuine_flood_collectors()).assess(ctx, product, thresholds)
    assert "satellite" not in [e.source for e in a.evidence]
