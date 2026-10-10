from __future__ import annotations

from dataclasses import dataclass, field

from claims_api.domain.models import Claim, Farmer, LandRecord, Policy, SowingRecord


@dataclass(frozen=True)
class ClaimContext:
    """Everything a product needs to judge one claim, loaded up front.

    Products stay pure functions of this context, which keeps them easy to test.
    """

    claim: Claim
    policy: Policy
    farmer: Farmer
    land_record: LandRecord | None
    sowing_record: SowingRecord | None
    other_claims: list[Claim] = field(default_factory=list)
