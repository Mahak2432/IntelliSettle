from claims_api.domain.models import (
    CheckResult,
    CheckStatus,
    EvidenceItem,
    ReviewThresholds,
    Signal,
    TruthScore,
    Verdict,
)


def decide_verdict(
    checks: list[CheckResult],
    truth: TruthScore,
    evidence: list[EvidenceItem],
    thresholds: ReviewThresholds,
) -> Verdict:
    """Map rules + AI score to the reviewer's fast lane. A human still makes every decision.

    - Looks suspicious (fast reject offered): any hard check failed, or the score is at or below the low bar.
    - Looks genuine (fast approve offered): every check passed, the score is at or above the high bar,
      at least one independent source confirms the event, and the score came from the AI (not a fallback).
    - Anything else needs a full review.
    """
    if any(c.status == CheckStatus.FAIL for c in checks):
        return Verdict.LOOKS_SUSPICIOUS
    if truth.score <= thresholds.suspicious_at_or_below:
        return Verdict.LOOKS_SUSPICIOUS

    all_passed = all(c.status == CheckStatus.PASS for c in checks)
    corroborated = any(e.independent and e.signal == Signal.SUPPORTS for e in evidence)
    if all_passed and corroborated and not truth.fallback and truth.score >= thresholds.genuine_at_or_above:
        return Verdict.LOOKS_GENUINE
    return Verdict.NEEDS_REVIEW
