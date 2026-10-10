"""The truth score: how genuine does this claim look, from 0 to 100?

The AI scorer reads every check and every piece of evidence and explains its
reasoning. The heuristic scorer is a transparent, deterministic baseline used
when the AI is unavailable (its results never unlock the fast-approve lane).
"""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel, Field

from claims_api.ai.gemini import GeminiClient
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import CheckResult, CheckStatus, EvidenceItem, Peril, Signal, TruthScore
from claims_api.products.base import InsuranceProduct

PERIL_EN = {Peril.FLOOD: "flood", Peril.EXCESS_RAIN: "heavy rain", Peril.HAILSTORM: "hailstorm"}
PERIL_HI = {Peril.FLOOD: "बाढ़", Peril.EXCESS_RAIN: "अत्यधिक बारिश", Peril.HAILSTORM: "ओलावृष्टि"}


class TruthScorer(Protocol):
    async def score(
        self,
        ctx: ClaimContext,
        product: InsuranceProduct,
        checks: list[CheckResult],
        evidence: list[EvidenceItem],
    ) -> TruthScore: ...


class AIScoreOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    reasons: list[str]
    red_flags: list[str]
    summary_en: str
    summary_hi: str


SYSTEM = """You are a senior crop-insurance claims investigator in India.
Score from 0 to 100 how likely it is that the claimed loss event really happened at this farm as described.
- 90-100: several independent sources confirm the event at this place and time, and nothing contradicts it.
- 70-89: credible support with minor gaps.
- 40-69: mixed or thin evidence; a person should look closely.
- 0-39: independent evidence contradicts the claim, or rules were broken.
Your score does not approve or pay anything. A human claims officer makes every decision.
In "reasons", give 2-5 short, specific points citing the evidence.
In "red_flags", list concrete concerns (or none).
Then write a message to the farmer in plain language: 2-3 short sentences on what was checked and what happens
next. Do not promise payment, do not use jargon, do not mention scores. summary_en in English;
summary_hi in simple Hindi (Devanagari)."""


def _claim_brief(ctx: ClaimContext, checks: list[CheckResult], evidence: list[EvidenceItem]) -> dict:
    plot = ctx.policy.plot
    return {
        "claim": {
            "peril": ctx.claim.peril,
            "crop": ctx.policy.crop,
            "season": ctx.policy.season,
            "loss_date": ctx.claim.loss_date.isoformat(),
            "submitted_at": ctx.claim.submitted_at.isoformat(),
            "farmer_description": ctx.claim.description,
            "location": f"{plot.village}, {plot.block}, {plot.district}, {plot.state}",
        },
        "hard_checks": [{"check": c.label, "status": c.status, "detail": c.detail} for c in checks],
        "evidence": [
            {
                "source": e.label,
                "independent_of_farmer": e.independent,
                "signal": e.signal,
                "summary": e.summary,
                "metrics": e.metrics,
            }
            for e in evidence
        ],
    }


class GeminiTruthScorer:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini

    async def score(self, ctx, product, checks, evidence) -> TruthScore:
        brief = _claim_brief(ctx, checks, evidence)
        prompt = (
            f"Domain guidance: {product.scoring_guidance(ctx.claim.peril)}\n\n"
            f"Claim file:\n{json.dumps(brief, ensure_ascii=False, indent=1, default=str)}"
        )
        result = await self.gemini.generate_json(
            namespace="gemini-truth-score", system=SYSTEM, prompt=prompt, schema=AIScoreOutput
        )
        out = AIScoreOutput.model_validate(result["data"])
        return TruthScore(**out.model_dump(), model=self.gemini.model)


class HeuristicTruthScorer:
    """Transparent points-based baseline. Same inputs as the AI, no reasoning beyond the weights."""

    BASE = 50
    INDEPENDENT = {Signal.SUPPORTS: 20, Signal.CONTRADICTS: -25}
    FARMER_PROVIDED = {Signal.SUPPORTS: 10, Signal.CONTRADICTS: -20}
    CHECK = {CheckStatus.FAIL: -30, CheckStatus.UNKNOWN: -5}

    async def score(self, ctx, product, checks, evidence) -> TruthScore:
        points = self.BASE
        reasons, flags = [], []
        for e in evidence:
            weights = self.INDEPENDENT if e.independent else self.FARMER_PROVIDED
            delta = weights.get(e.signal, 0)
            points += delta
            if delta > 0:
                reasons.append(f"{e.label}: {e.summary}")
            elif delta < 0:
                flags.append(f"{e.label}: {e.summary}")
        for c in checks:
            points += self.CHECK.get(c.status, 0)
            if c.status == CheckStatus.FAIL:
                flags.append(f"{c.label}: {c.detail}")
        score = max(0, min(100, points))

        confirmed = sum(1 for e in evidence if e.independent and e.signal == Signal.SUPPORTS)
        independent = sum(1 for e in evidence if e.independent and e.signal != Signal.UNAVAILABLE)
        if not confirmed:
            flags.insert(0, "No independent source confirmed the event.")
        peril = ctx.claim.peril
        return TruthScore(
            score=score,
            reasons=reasons,
            red_flags=flags,
            summary_en=(
                f"We checked your claim against {independent} independent data sources; {confirmed} "
                f"confirmed the {PERIL_EN[peril]} near your farm. A claims officer will review it shortly."
            ),
            summary_hi=(
                f"हमने आपके दावे की जाँच {independent} स्वतंत्र स्रोतों से की; {confirmed} स्रोतों ने आपके खेत "
                f"के पास {PERIL_HI[peril]} की पुष्टि की। एक दावा अधिकारी जल्द ही इसकी समीक्षा करेगा।"
            ),
            model="heuristic-v1",
        )
