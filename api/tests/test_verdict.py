from claims_api.domain.models import (
    CheckResult,
    CheckStatus,
    ReviewThresholds,
    Signal,
    TruthScore,
    Verdict,
)
from claims_api.engine.verdict import decide_verdict
from tests import factories as f

T = ReviewThresholds(genuine_at_or_above=80, suspicious_at_or_below=30)


def check(status: CheckStatus) -> CheckResult:
    return CheckResult(code="x", label="x", status=status, detail="")


def truth(score: int, fallback: bool = False) -> TruthScore:
    return TruthScore(
        score=score, reasons=[], red_flags=[], summary_en="", summary_hi="", model="t", fallback=fallback
    )


CONFIRMED = [f.evidence("satellite", Signal.SUPPORTS)]


def test_high_score_with_clean_checks_and_corroboration_looks_genuine():
    assert decide_verdict([check(CheckStatus.PASS)], truth(85), CONFIRMED, T) == Verdict.LOOKS_GENUINE


def test_benchmark_is_inclusive():
    assert decide_verdict([check(CheckStatus.PASS)], truth(80), CONFIRMED, T) == Verdict.LOOKS_GENUINE
    assert decide_verdict([check(CheckStatus.PASS)], truth(30), CONFIRMED, T) == Verdict.LOOKS_SUSPICIOUS


def test_any_failed_check_looks_suspicious_even_with_high_score():
    checks = [check(CheckStatus.PASS), check(CheckStatus.FAIL)]
    assert decide_verdict(checks, truth(95), CONFIRMED, T) == Verdict.LOOKS_SUSPICIOUS


def test_low_score_looks_suspicious():
    assert decide_verdict([check(CheckStatus.PASS)], truth(20), CONFIRMED, T) == Verdict.LOOKS_SUSPICIOUS


def test_unknown_check_blocks_fast_approve():
    checks = [check(CheckStatus.PASS), check(CheckStatus.UNKNOWN)]
    assert decide_verdict(checks, truth(95), CONFIRMED, T) == Verdict.NEEDS_REVIEW


def test_high_score_without_independent_confirmation_needs_review():
    farmer_only = [f.evidence("photo", Signal.SUPPORTS, independent=False)]
    assert decide_verdict([check(CheckStatus.PASS)], truth(95), farmer_only, T) == Verdict.NEEDS_REVIEW


def test_fallback_score_never_unlocks_fast_approve():
    assert decide_verdict([check(CheckStatus.PASS)], truth(95, True), CONFIRMED, T) == Verdict.NEEDS_REVIEW


def test_thresholds_are_configurable():
    strict = ReviewThresholds(genuine_at_or_above=90, suspicious_at_or_below=10)
    assert decide_verdict([check(CheckStatus.PASS)], truth(85), CONFIRMED, strict) == Verdict.NEEDS_REVIEW
