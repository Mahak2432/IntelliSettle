"""Core domain model shared by every insurance product.

Product-specific rules live in `claims_api.products`; nothing in this module
knows about crops, rainfall or satellites.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

Language = Literal["hi", "en"]


class Peril(StrEnum):
    FLOOD = "flood"
    EXCESS_RAIN = "excess_rain"
    HAILSTORM = "hailstorm"


class GeoPoint(BaseModel):
    lat: float
    lon: float


# --- Reference data (comes from insurer + government registries) -----------------


class BankAccount(BaseModel):
    account_holder: str
    account_masked: str
    ifsc: str
    bank_name: str


class Farmer(BaseModel):
    farmer_id: str
    name: str
    name_hi: str
    father_name: str
    phone: str
    preferred_language: Language = "hi"
    bank: BankAccount
    # Demo farmers live on the date of a real past disaster so their claims can be filed "on time".
    demo_today: date | None = None


class Plot(BaseModel):
    khasra_no: str
    village: str
    block: str
    district: str
    state: str
    area_ha: float
    location: GeoPoint


class Policy(BaseModel):
    policy_no: str
    product_code: str
    farmer_id: str
    insurer: str
    scheme: str
    season: str
    crop: str
    plot: Plot
    insured_area_ha: float
    sum_insured_inr: int
    cover_start: date
    cover_end: date
    perils: list[Peril]


class LandRecord(BaseModel):
    """One row of a state land-record register (Bhulekh / Khatauni)."""

    khasra_no: str
    village: str
    district: str
    owner_farmer_id: str
    owner_name_hi: str
    area_ha: float


class SowingRecord(BaseModel):
    """One row of the crop sowing registry (AgriStack crop survey)."""

    farmer_id: str
    khasra_no: str
    season: str
    crop: str


# --- Claim intake -----------------------------------------------------------------


class Photo(BaseModel):
    photo_id: str
    storage_path: str
    sha256: str
    phash: str | None = None
    exif_captured_at: datetime | None = None
    exif_location: GeoPoint | None = None
    # Phone browsers often strip EXIF GPS, so the app also records where and when
    # the photo was taken using the device's own clock and geolocation.
    device_captured_at: datetime | None = None
    device_location: GeoPoint | None = None

    @property
    def location(self) -> GeoPoint | None:
        return self.exif_location or self.device_location

    @property
    def captured_at(self) -> datetime | None:
        return self.exif_captured_at or self.device_captured_at


DocumentKind = Literal["land_record", "bank_passbook", "policy"]


class ExtractedField(BaseModel):
    value: str | None
    confidence: float = Field(ge=0, le=1)


class DocumentExtraction(BaseModel):
    kind: DocumentKind
    language: str | None = None
    fields: dict[str, ExtractedField]
    model: str


class DocumentUpload(BaseModel):
    document_id: str
    kind: DocumentKind
    storage_path: str
    extraction: DocumentExtraction | None = None


# --- Assessment -------------------------------------------------------------------


class CheckStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class CheckResult(BaseModel):
    """A deterministic pass/fail rule. Any FAIL blocks the fast-approve lane."""

    code: str
    label: str
    status: CheckStatus
    detail: str
    data: dict[str, Any] = Field(default_factory=dict)


class Signal(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    INCONCLUSIVE = "inconclusive"
    UNAVAILABLE = "unavailable"


class Citation(BaseModel):
    title: str
    url: str
    published: str | None = None


class EvidenceItem(BaseModel):
    """What one independent source says about whether the loss event happened."""

    source: str
    label: str
    signal: Signal
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    citations: list[Citation] = Field(default_factory=list)
    independent: bool = True
    # Images for the reviewer (e.g. radar before/after). Never sent to the AI scorer.
    visuals: dict[str, str] = Field(default_factory=dict)


class TruthScore(BaseModel):
    score: int = Field(ge=0, le=100)
    reasons: list[str]
    red_flags: list[str]
    summary_en: str
    summary_hi: str
    model: str
    fallback: bool = False


class Verdict(StrEnum):
    LOOKS_GENUINE = "looks_genuine"
    NEEDS_REVIEW = "needs_review"
    LOOKS_SUSPICIOUS = "looks_suspicious"


class PayoutQuote(BaseModel):
    sum_insured_inr: int
    payout_percent: float
    amount_inr: int
    basis: str


class Assessment(BaseModel):
    product_code: str
    checks: list[CheckResult]
    evidence: list[EvidenceItem]
    truth: TruthScore
    verdict: Verdict
    payout_quote: PayoutQuote
    thresholds: ReviewThresholds
    assessed_at: datetime


class ReviewThresholds(BaseModel):
    genuine_at_or_above: int = Field(default=80, ge=0, le=100)
    suspicious_at_or_below: int = Field(default=30, ge=0, le=100)


# --- Decisions, payouts, appeals --------------------------------------------------


class ClaimStatus(StrEnum):
    SUBMITTED = "submitted"
    ASSESSING = "assessing"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    APPEALED = "appealed"


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject"]
    fast_lane: bool
    reason: str | None
    reviewer_id: str
    decided_at: datetime
    verdict_at_decision: Verdict
    score_at_decision: int


class PayoutRecord(BaseModel):
    amount_inr: int
    reference: str
    rail: str
    account_masked: str
    paid_at: datetime


class Appeal(BaseModel):
    message: str
    filed_at: datetime


class TimelineEvent(BaseModel):
    at: datetime
    status: ClaimStatus
    note: str


class Claim(BaseModel):
    claim_id: str
    policy_no: str
    farmer_id: str
    product_code: str
    # Demo isolation: the browser session that filed the claim. None = shared by everyone.
    sandbox: str | None = None
    peril: Peril
    loss_date: date
    submitted_at: datetime
    description: str
    language: Language = "hi"
    filed_from: GeoPoint | None = None
    photos: list[Photo] = Field(default_factory=list)
    documents: list[DocumentUpload] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.SUBMITTED
    assessment: Assessment | None = None
    decisions: list[ReviewDecision] = Field(default_factory=list)
    payout: PayoutRecord | None = None
    appeal: Appeal | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)


Assessment.model_rebuild()
