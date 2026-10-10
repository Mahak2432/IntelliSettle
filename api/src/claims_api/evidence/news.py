"""Local news corroboration using Gemini with Google Search grounding."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from claims_api.ai.gemini import GeminiClient
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import Citation, EvidenceItem, Signal
from claims_api.evidence.base import PERIL_WORDS, EvidenceCollector, date_window

SYSTEM = (
    "You verify insurance claims for Indian farmers by checking whether news outlets or government "
    "bulletins reported a weather disaster at a given place and time. Use Google Search. Report only "
    "what the sources actually say. If nothing relevant is found, say so; never guess or invent reports."
)


class NewsReport(BaseModel):
    title: str
    publisher: str
    published_date: str | None
    relevant_fact: str


class NewsFindings(BaseModel):
    event_reported: bool
    location_match: Literal["village", "block", "district", "state", "none"]
    dates_match: bool
    summary: str
    reports: list[NewsReport]


class NewsCollector(EvidenceCollector):
    name = "news"
    label = "News and government reports"

    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini

    async def collect(self, ctx: ClaimContext) -> EvidenceItem:
        plot = ctx.policy.plot
        start, end = date_window(ctx.claim.loss_date, days_before=3, days_after=3)
        prompt = (
            f"Did any news report or government bulletin describe a {PERIL_WORDS[ctx.claim.peril]} "
            f"affecting {plot.village} village, {plot.block} block, {plot.district} district, "
            f"{plot.state}, India, between {start:%d %B %Y} and {end:%d %B %Y}? Search in English and "
            "Hindi. Set location_match to the most specific level a source mentions (village, block, "
            "district or state) and dates_match to whether the reported dates fall in that window."
        )
        result = await self.gemini.generate_json(
            namespace="gemini-news", system=SYSTEM, prompt=prompt, schema=NewsFindings, google_search=True
        )
        findings = NewsFindings.model_validate(result["data"])
        citations = [Citation(title=s["title"], url=s["url"]) for s in result["sources"]]
        return interpret(findings, citations, self.label)


def interpret(findings: NewsFindings, citations: list[Citation], label: str) -> EvidenceItem:
    local = findings.location_match in ("village", "block", "district")
    metrics = {
        "event_reported": findings.event_reported,
        "location_match": findings.location_match,
        "dates_match": findings.dates_match,
        "reports": [r.model_dump() for r in findings.reports],
    }
    if findings.event_reported and not citations:
        signal = Signal.INCONCLUSIVE
        summary = "The model described reports but search returned no verifiable sources, so it is ignored."
    elif findings.event_reported and local and findings.dates_match:
        signal = Signal.SUPPORTS
        summary = findings.summary
    else:
        signal = Signal.INCONCLUSIVE
        summary = findings.summary or "No matching local reports were found."
    return EvidenceItem(
        source="news", label=label, signal=signal, summary=summary, metrics=metrics, citations=citations
    )
