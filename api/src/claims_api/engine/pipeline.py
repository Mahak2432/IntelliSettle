"""Runs one claim through documents -> hard checks -> evidence -> truth score -> verdict -> payout quote."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from datetime import UTC, datetime

from claims_api.ai.documents import DocumentReader
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import Assessment, Claim, EvidenceItem, ReviewThresholds, Signal
from claims_api.engine.scoring import TruthScorer
from claims_api.engine.verdict import decide_verdict
from claims_api.evidence.base import EvidenceCollector
from claims_api.products.base import InsuranceProduct

log = logging.getLogger(__name__)


class ClaimAssessor:
    def __init__(
        self,
        collectors: dict[str, EvidenceCollector],
        scorer: TruthScorer,
        fallback_scorer: TruthScorer,
        document_reader: DocumentReader | None = None,
    ) -> None:
        self.collectors = collectors
        self.scorer = scorer
        self.fallback_scorer = fallback_scorer
        self.document_reader = document_reader

    async def assess(
        self, ctx: ClaimContext, product: InsuranceProduct, thresholds: ReviewThresholds
    ) -> tuple[Claim, Assessment]:
        claim = await self._read_documents(ctx.claim)
        ctx = replace(ctx, claim=claim)

        checks = product.hard_checks(ctx)
        plan = product.evidence_plan(claim.peril)
        evidence = list(await asyncio.gather(*(self._collect(name, ctx) for name in plan)))

        try:
            truth = await self.scorer.score(ctx, product, checks, evidence)
        except Exception:
            log.exception("AI truth scoring failed for claim %s; using heuristic fallback", claim.claim_id)
            truth = await self.fallback_scorer.score(ctx, product, checks, evidence)
            truth = truth.model_copy(update={"fallback": True})

        assessment = Assessment(
            product_code=product.code,
            checks=checks,
            evidence=evidence,
            truth=truth,
            verdict=decide_verdict(checks, truth, evidence, thresholds),
            payout_quote=product.payout_quote(ctx, evidence),
            thresholds=thresholds,
            assessed_at=datetime.now(UTC),
        )
        return claim, assessment

    async def _collect(self, name: str, ctx: ClaimContext) -> EvidenceItem:
        collector = self.collectors.get(name)
        if collector is None:
            return EvidenceItem(
                source=name, label=name, signal=Signal.UNAVAILABLE, summary="Source not configured."
            )
        try:
            return await collector.collect(ctx)
        except Exception as exc:
            log.exception("Evidence source %s failed for claim %s", name, ctx.claim.claim_id)
            return collector.unavailable(f"Source could not be reached ({type(exc).__name__}).")

    async def _read_documents(self, claim: Claim) -> Claim:
        if self.document_reader is None:
            return claim
        documents = []
        for doc in claim.documents:
            if doc.extraction is None:
                try:
                    doc = doc.model_copy(update={"extraction": await self.document_reader.read(doc)})
                except Exception:
                    log.exception("Could not read document %s on claim %s", doc.document_id, claim.claim_id)
            documents.append(doc)
        return claim.model_copy(update={"documents": documents})
