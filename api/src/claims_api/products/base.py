"""The plug-in contract every insurance product implements.

Adding a new line of business (livestock, health, motor...) means writing one
new `InsuranceProduct` subclass and registering it. The claim pipeline, truth
scoring, reviewer workflow and payouts are shared and never change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from claims_api.domain.context import ClaimContext
from claims_api.domain.models import CheckResult, EvidenceItem, PayoutQuote, Peril


class InsuranceProduct(ABC):
    code: ClassVar[str]
    name: ClassVar[str]
    perils: ClassVar[tuple[Peril, ...]]

    @abstractmethod
    def evidence_plan(self, peril: Peril) -> list[str]:
        """Names of the evidence collectors to run for a claim of this peril."""

    @abstractmethod
    def hard_checks(self, ctx: ClaimContext) -> list[CheckResult]:
        """Deterministic pass/fail rules. No AI, no network calls."""

    @abstractmethod
    def payout_quote(self, ctx: ClaimContext, evidence: list[EvidenceItem]) -> PayoutQuote:
        """The amount payable if a reviewer approves. Always computed by code from policy terms."""

    @abstractmethod
    def scoring_guidance(self, peril: Peril) -> str:
        """Domain hints for the AI truth scorer: what strong and weak evidence look like."""
