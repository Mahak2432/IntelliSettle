"""Claim lifecycle: submit -> AI assessment -> human review -> payout, with one appeal."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime

from claims_api.domain.context import ClaimContext
from claims_api.domain.models import (
    Appeal,
    Claim,
    ClaimStatus,
    DocumentKind,
    DocumentUpload,
    GeoPoint,
    Language,
    Peril,
    Photo,
    ReviewDecision,
    TimelineEvent,
    Verdict,
)
from claims_api.domain.time import IST
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.infra.storage import BlobStore
from claims_api.intake.photos import inspect_photo
from claims_api.products.registry import get_product
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.store.claims import ClaimRepository, ThresholdStore

MIN_REASON_LENGTH = 10
REVIEWABLE = {ClaimStatus.READY_FOR_REVIEW, ClaimStatus.APPEALED}
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class ClaimError(ValueError):
    """A request that breaks a business rule. The message is safe to show to users."""


@dataclass(frozen=True)
class NewPhoto:
    data: bytes
    content_type: str = "image/jpeg"
    device_captured_at: datetime | None = None
    device_location: GeoPoint | None = None


@dataclass(frozen=True)
class NewDocument:
    kind: DocumentKind
    data: bytes
    content_type: str = "image/jpeg"


def _now() -> datetime:
    return datetime.now(UTC)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%y%m%d}-{secrets.token_hex(3).upper()}"


class ClaimService:
    def __init__(
        self,
        repo: ClaimRepository,
        reference: ReferenceData,
        assessor: ClaimAssessor,
        blobs: BlobStore,
        thresholds: ThresholdStore,
        payouts: SimulatedPayoutRail,
        clock=_now,
    ) -> None:
        self.repo = repo
        self.reference = reference
        self.assessor = assessor
        self.blobs = blobs
        self.thresholds = thresholds
        self.payouts = payouts
        self.clock = clock

    def now_for(self, farmer_id: str) -> datetime:
        """Current time, shifted onto the demo date for demo farmers."""
        now = self.clock()
        farmer = self.reference.farmer(farmer_id)
        if farmer and farmer.demo_today:
            return now + (farmer.demo_today - now.astimezone(IST).date())
        return now

    # --- Farmer actions -------------------------------------------------------------

    async def submit(
        self,
        *,
        farmer_id: str,
        policy_no: str,
        peril: Peril,
        loss_date: date,
        description: str,
        language: Language = "hi",
        filed_from: GeoPoint | None = None,
        photos: list[NewPhoto] = (),
        documents: list[NewDocument] = (),
    ) -> Claim:
        policy = self.reference.policy(policy_no)
        if policy is None or policy.farmer_id != farmer_id:
            raise ClaimError("Policy not found for this farmer.")
        if not photos:
            raise ClaimError("Add at least one photo of the damage.")

        claim_id = _new_id("CLM")
        stored_photos = [await self._store_photo(claim_id, i, p) for i, p in enumerate(photos, 1)]
        stored_docs = [await self._store_document(claim_id, i, d) for i, d in enumerate(documents, 1)]
        now = self.now_for(farmer_id)
        claim = Claim(
            claim_id=claim_id,
            policy_no=policy_no,
            farmer_id=farmer_id,
            product_code=policy.product_code,
            peril=peril,
            loss_date=loss_date,
            submitted_at=now,
            description=description.strip(),
            language=language,
            filed_from=filed_from,
            photos=stored_photos,
            documents=stored_docs,
            timeline=[TimelineEvent(at=now, status=ClaimStatus.SUBMITTED, note="Claim received.")],
        )
        await self.repo.save(claim)
        return claim

    async def appeal(self, claim_id: str, farmer_id: str, message: str) -> Claim:
        claim = await self._get(claim_id)
        if claim.farmer_id != farmer_id:
            raise ClaimError("Claim not found.")
        if claim.status != ClaimStatus.REJECTED:
            raise ClaimError("Only a rejected claim can be appealed.")
        if claim.appeal is not None:
            raise ClaimError("This claim has already been appealed once.")
        if len(message.strip()) < MIN_REASON_LENGTH:
            raise ClaimError("Please explain why you are appealing.")
        claim.appeal = Appeal(message=message.strip(), filed_at=self.now_for(farmer_id))
        self._move(claim, ClaimStatus.APPEALED, "Appeal filed; a senior officer will review the claim again.")
        await self.repo.save(claim)
        return claim

    # --- System actions -------------------------------------------------------------

    async def assess(self, claim_id: str) -> Claim:
        claim = await self._get(claim_id)
        self._move(claim, ClaimStatus.ASSESSING, "AI verification started.")
        await self.repo.save(claim)

        ctx = await self.context_for(claim)
        product = get_product(claim.product_code)
        claim, assessment = await self.assessor.assess(ctx, product, await self.thresholds.get())
        claim.assessment = assessment
        self._move(claim, ClaimStatus.READY_FOR_REVIEW, "AI verification complete; waiting for an officer.")
        await self.repo.save(claim)
        return claim

    async def context_for(self, claim: Claim) -> ClaimContext:
        policy = self.reference.policy(claim.policy_no)
        farmer = self.reference.farmer(claim.farmer_id)
        if policy is None or farmer is None:
            raise ClaimError("Claim references unknown policy or farmer.")
        return ClaimContext(
            claim=claim,
            policy=policy,
            farmer=farmer,
            land_record=self.reference.land_record(policy.plot.village, policy.plot.khasra_no),
            sowing_record=self.reference.sowing_record(
                farmer.farmer_id, policy.plot.khasra_no, policy.season
            ),
            other_claims=[c for c in await self.repo.list() if c.claim_id != claim.claim_id],
        )

    # --- Reviewer actions -----------------------------------------------------------

    async def decide(
        self,
        claim_id: str,
        *,
        action: str,
        fast_lane: bool,
        reason: str | None,
        reviewer_id: str,
    ) -> Claim:
        claim = await self._get(claim_id)
        if claim.status not in REVIEWABLE:
            raise ClaimError(f"Claim is {claim.status}; it cannot be decided now.")
        if claim.assessment is None:
            raise ClaimError("Claim has not been assessed yet.")
        if action not in ("approve", "reject"):
            raise ClaimError("Action must be approve or reject.")

        verdict = claim.assessment.verdict
        reason = (reason or "").strip() or None
        if fast_lane:
            if claim.status == ClaimStatus.APPEALED:
                raise ClaimError("Appeals always get a full review.")
            allowed = Verdict.LOOKS_GENUINE if action == "approve" else Verdict.LOOKS_SUSPICIOUS
            if verdict != allowed:
                raise ClaimError(
                    f"Fast {action} is only available when the claim {allowed.replace('_', ' ')}."
                )
        elif reason is None or len(reason) < MIN_REASON_LENGTH:
            raise ClaimError("Give a reason (at least 10 characters) for a full-review decision.")

        amount = claim.assessment.payout_quote.amount_inr
        if action == "approve" and amount <= 0:
            raise ClaimError("No payout trigger was met, so there is nothing to pay.")

        claim.decisions.append(
            ReviewDecision(
                action=action,
                fast_lane=fast_lane,
                reason=reason,
                reviewer_id=reviewer_id,
                decided_at=self.now_for(claim.farmer_id),
                verdict_at_decision=verdict,
                score_at_decision=claim.assessment.truth.score,
            )
        )
        if action == "reject":
            self._move(
                claim, ClaimStatus.REJECTED, reason or "Rejected: independent evidence did not support it."
            )
        else:
            self._move(claim, ClaimStatus.APPROVED, f"Approved for ₹{amount:,}.")
            farmer = self.reference.farmer(claim.farmer_id)
            claim.payout = await self.payouts.pay(amount, farmer, at=self.now_for(claim.farmer_id))
            self._move(
                claim,
                ClaimStatus.PAID,
                f"₹{amount:,} sent to account {farmer.bank.account_masked} (ref {claim.payout.reference}).",
            )
        await self.repo.save(claim)
        return claim

    # --- Helpers --------------------------------------------------------------------

    async def _get(self, claim_id: str) -> Claim:
        claim = await self.repo.get(claim_id)
        if claim is None:
            raise ClaimError("Claim not found.")
        return claim

    def _move(self, claim: Claim, status: ClaimStatus, note: str) -> None:
        claim.status = status
        claim.timeline.append(TimelineEvent(at=self.now_for(claim.farmer_id), status=status, note=note))

    async def _store_photo(self, claim_id: str, index: int, photo: NewPhoto) -> Photo:
        facts = inspect_photo(photo.data)
        ext = EXTENSIONS.get(photo.content_type, "jpg")
        path = f"claims/{claim_id}/photos/{index}.{ext}"
        await self.blobs.put(path, photo.data, photo.content_type)
        return Photo(
            photo_id=f"{claim_id}-P{index}",
            storage_path=path,
            sha256=facts.sha256,
            phash=facts.phash,
            exif_captured_at=facts.captured_at,
            exif_location=facts.location,
            device_captured_at=photo.device_captured_at,
            device_location=photo.device_location,
        )

    async def _store_document(self, claim_id: str, index: int, doc: NewDocument) -> DocumentUpload:
        ext = EXTENSIONS.get(doc.content_type, "jpg")
        path = f"claims/{claim_id}/documents/{index}-{doc.kind}.{ext}"
        await self.blobs.put(path, doc.data, doc.content_type)
        return DocumentUpload(document_id=f"{claim_id}-D{index}", kind=doc.kind, storage_path=path)
