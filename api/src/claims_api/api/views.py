"""Response shapes. Farmers never see scores or reviewer notes; officers see everything."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from claims_api.domain.models import (
    Appeal,
    Claim,
    ClaimStatus,
    Farmer,
    PayoutRecord,
    Peril,
    Policy,
    TimelineEvent,
    Verdict,
)


class FarmerClaimView(BaseModel):
    claim_id: str
    policy_no: str
    peril: Peril
    loss_date: date
    submitted_at: datetime
    status: ClaimStatus
    description: str
    message_en: str | None
    message_hi: str | None
    decision_reason: str | None
    payout: PayoutRecord | None
    appeal: Appeal | None
    can_appeal: bool
    timeline: list[TimelineEvent]
    photo_count: int

    @classmethod
    def of(cls, claim: Claim) -> FarmerClaimView:
        truth = claim.assessment.truth if claim.assessment else None
        last = claim.decisions[-1] if claim.decisions else None
        return cls(
            claim_id=claim.claim_id,
            policy_no=claim.policy_no,
            peril=claim.peril,
            loss_date=claim.loss_date,
            submitted_at=claim.submitted_at,
            status=claim.status,
            description=claim.description,
            message_en=truth.summary_en if truth else None,
            message_hi=truth.summary_hi if truth else None,
            decision_reason=last.reason if last and last.action == "reject" else None,
            payout=claim.payout,
            appeal=claim.appeal,
            can_appeal=claim.status == ClaimStatus.REJECTED and claim.appeal is None,
            timeline=claim.timeline,
            photo_count=len(claim.photos),
        )


class ReviewQueueItem(BaseModel):
    claim_id: str
    farmer_name: str
    village: str
    district: str
    crop: str
    peril: Peril
    loss_date: date
    submitted_at: datetime
    status: ClaimStatus
    score: int | None
    verdict: Verdict | None
    amount_inr: int | None
    appealed: bool

    @classmethod
    def of(cls, claim: Claim, farmer: Farmer, policy: Policy) -> ReviewQueueItem:
        a = claim.assessment
        return cls(
            claim_id=claim.claim_id,
            farmer_name=farmer.name,
            village=policy.plot.village,
            district=policy.plot.district,
            crop=policy.crop,
            peril=claim.peril,
            loss_date=claim.loss_date,
            submitted_at=claim.submitted_at,
            status=claim.status,
            score=a.truth.score if a else None,
            verdict=a.verdict if a else None,
            amount_inr=a.payout_quote.amount_inr if a else None,
            appealed=claim.appeal is not None,
        )


class ReviewClaimView(BaseModel):
    claim: Claim
    farmer: Farmer
    policy: Policy
