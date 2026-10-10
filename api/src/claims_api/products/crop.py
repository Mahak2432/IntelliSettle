"""Product #1: parametric crop micro-insurance (PMFBY / RWBCIS style)."""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta

import imagehash

from claims_api.domain.context import ClaimContext
from claims_api.domain.geo import distance_km
from claims_api.domain.models import (
    CheckResult,
    CheckStatus,
    ClaimStatus,
    DocumentExtraction,
    EvidenceItem,
    PayoutQuote,
    Peril,
)
from claims_api.domain.time import IST
from claims_api.products.base import InsuranceProduct

IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


@dataclass(frozen=True)
class Slab:
    at_or_above: float
    percent: float


@dataclass(frozen=True)
class CropTermSheet:
    """Policy terms. In production this would be loaded per scheme, season and district."""

    excess_rain_slabs_mm_24h: tuple[Slab, ...] = (Slab(100, 25), Slab(150, 50), Slab(200, 100))
    flood_slabs_fraction: tuple[Slab, ...] = (Slab(0.10, 25), Slab(0.25, 50), Slab(0.50, 100))
    hailstorm_flat_percent: float = 50
    intimation_days: int = 3
    photo_radius_km: float = 1.0
    photo_grace_days_before_loss: int = 1
    duplicate_window_days: int = 7
    reused_photo_max_distance: int = 6
    min_extraction_confidence: float = 0.85
    name_match_ratio: float = 0.8
    evidence_plans: dict[Peril, tuple[str, ...]] = field(
        default_factory=lambda: {
            Peril.FLOOD: ("weather", "satellite", "news", "photo"),
            Peril.EXCESS_RAIN: ("weather", "satellite", "news", "photo"),
            Peril.HAILSTORM: ("weather", "news", "photo"),
        }
    )


def slab_percent(value: float | None, slabs: tuple[Slab, ...]) -> tuple[float, Slab | None]:
    if value is None:
        return 0.0, None
    hit = None
    for slab in sorted(slabs, key=lambda s: s.at_or_above):
        if value >= slab.at_or_above:
            hit = slab
    return (hit.percent, hit) if hit else (0.0, None)


def _metric(evidence: list[EvidenceItem], source: str, key: str) -> float | None:
    for item in evidence:
        if item.source == source and key in item.metrics and item.metrics[key] is not None:
            return float(item.metrics[key])
    return None


def _normalise(text: str) -> str:
    return "".join(unicodedata.normalize("NFC", text).split()).casefold()


def _check(code: str, label: str, status: CheckStatus, detail: str, **data) -> CheckResult:
    return CheckResult(code=code, label=label, status=status, detail=detail, data=data)


class CropParametricProduct(InsuranceProduct):
    code = "crop-parametric-v1"
    name = "Parametric Crop Micro-Insurance"
    perils = (Peril.FLOOD, Peril.EXCESS_RAIN, Peril.HAILSTORM)

    def __init__(self, terms: CropTermSheet | None = None) -> None:
        self.terms = terms or CropTermSheet()

    def evidence_plan(self, peril: Peril) -> list[str]:
        return list(self.terms.evidence_plans[peril])

    # --- Hard checks --------------------------------------------------------------

    def hard_checks(self, ctx: ClaimContext) -> list[CheckResult]:
        return [
            self._peril_covered(ctx),
            self._policy_active(ctx),
            self._reported_in_time(ctx),
            self._land_record_match(ctx),
            self._crop_sown_match(ctx),
            self._photo_at_plot(ctx),
            self._photo_after_loss(ctx),
            self._no_duplicate_claim(ctx),
            self._no_reused_photo(ctx),
            self._documents_match_records(ctx),
        ]

    def _peril_covered(self, ctx: ClaimContext) -> CheckResult:
        label = "Peril is covered by the policy"
        if ctx.claim.peril in ctx.policy.perils:
            return _check("peril_covered", label, CheckStatus.PASS, f"{ctx.claim.peril} is covered.")
        return _check(
            "peril_covered", label, CheckStatus.FAIL, f"{ctx.claim.peril} is not covered by this policy."
        )

    def _policy_active(self, ctx: ClaimContext) -> CheckResult:
        label = "Policy active on the loss date"
        p, loss = ctx.policy, ctx.claim.loss_date
        if p.cover_start <= loss <= p.cover_end:
            return _check(
                "policy_active", label, CheckStatus.PASS, f"Cover runs {p.cover_start} to {p.cover_end}."
            )
        return _check(
            "policy_active",
            label,
            CheckStatus.FAIL,
            f"Loss date {loss} is outside cover period {p.cover_start} to {p.cover_end}.",
        )

    def _reported_in_time(self, ctx: ClaimContext) -> CheckResult:
        label = f"Reported within {self.terms.intimation_days * 24} hours"
        submitted = ctx.claim.submitted_at.astimezone(IST).date()
        days = (submitted - ctx.claim.loss_date).days
        if days < 0:
            return _check(
                "reported_in_time", label, CheckStatus.FAIL, "Loss date is after the submission date."
            )
        if days <= self.terms.intimation_days:
            return _check(
                "reported_in_time",
                label,
                CheckStatus.PASS,
                f"Reported {days} day(s) after the loss.",
                days=days,
            )
        return _check(
            "reported_in_time",
            label,
            CheckStatus.FAIL,
            f"Reported {days} days after the loss; the limit is {self.terms.intimation_days} days.",
            days=days,
        )

    def _land_record_match(self, ctx: ClaimContext) -> CheckResult:
        label = "Land record confirms ownership and area"
        rec = ctx.land_record
        if rec is None:
            return _check(
                "land_record_match",
                label,
                CheckStatus.FAIL,
                f"Khasra {ctx.policy.plot.khasra_no} not found in the land register.",
            )
        if rec.owner_farmer_id != ctx.policy.farmer_id:
            return _check(
                "land_record_match",
                label,
                CheckStatus.FAIL,
                "The land register lists a different owner for this plot.",
            )
        if ctx.policy.insured_area_ha > rec.area_ha + 0.01:
            return _check(
                "land_record_match",
                label,
                CheckStatus.FAIL,
                f"Insured area {ctx.policy.insured_area_ha} ha exceeds recorded area {rec.area_ha} ha.",
            )
        return _check(
            "land_record_match",
            label,
            CheckStatus.PASS,
            f"Owner matches; recorded area {rec.area_ha} ha covers insured {ctx.policy.insured_area_ha} ha.",
        )

    def _crop_sown_match(self, ctx: ClaimContext) -> CheckResult:
        label = "Crop survey confirms the insured crop"
        rec = ctx.sowing_record
        if rec is None:
            return _check(
                "crop_sown_match",
                label,
                CheckStatus.UNKNOWN,
                f"No crop survey entry for khasra {ctx.policy.plot.khasra_no} in {ctx.policy.season}.",
            )
        if _normalise(rec.crop) != _normalise(ctx.policy.crop):
            return _check(
                "crop_sown_match",
                label,
                CheckStatus.FAIL,
                f"Policy says {ctx.policy.crop} but the crop survey recorded {rec.crop}.",
            )
        return _check(
            "crop_sown_match", label, CheckStatus.PASS, f"Crop survey recorded {rec.crop} for this plot."
        )

    def _photo_at_plot(self, ctx: ClaimContext) -> CheckResult:
        label = f"Photos taken within {self.terms.photo_radius_km:g} km of the plot"
        located = [p for p in ctx.claim.photos if p.location is not None]
        if not located:
            return _check("photo_at_plot", label, CheckStatus.UNKNOWN, "No photo carries a location.")
        distances = {p.photo_id: round(distance_km(p.location, ctx.policy.plot.location), 3) for p in located}
        nearest = min(distances.values())
        if nearest <= self.terms.photo_radius_km:
            return _check(
                "photo_at_plot",
                label,
                CheckStatus.PASS,
                f"Nearest photo was taken {nearest:.2f} km from the plot.",
                distances_km=distances,
            )
        return _check(
            "photo_at_plot",
            label,
            CheckStatus.FAIL,
            f"Nearest photo was taken {nearest:.1f} km from the plot.",
            distances_km=distances,
        )

    def _photo_after_loss(self, ctx: ClaimContext) -> CheckResult:
        label = "Photos taken after the loss event"
        timed = [p for p in ctx.claim.photos if p.captured_at is not None]
        if not timed:
            return _check("photo_after_loss", label, CheckStatus.UNKNOWN, "No photo carries a capture time.")
        earliest_allowed = ctx.claim.loss_date - timedelta(days=self.terms.photo_grace_days_before_loss)
        early = [p.photo_id for p in timed if p.captured_at.astimezone(IST).date() < earliest_allowed]
        if early:
            return _check(
                "photo_after_loss",
                label,
                CheckStatus.FAIL,
                f"{len(early)} photo(s) were taken before the claimed loss date.",
                photo_ids=early,
            )
        return _check(
            "photo_after_loss", label, CheckStatus.PASS, "All photos were taken on or after the loss date."
        )

    def _no_duplicate_claim(self, ctx: ClaimContext) -> CheckResult:
        label = "No duplicate claim for the same loss"
        window = self.terms.duplicate_window_days
        dupes = [
            c.claim_id
            for c in ctx.other_claims
            if c.claim_id != ctx.claim.claim_id
            and c.policy_no == ctx.claim.policy_no
            and c.peril == ctx.claim.peril
            and c.status != ClaimStatus.REJECTED
            and abs((c.loss_date - ctx.claim.loss_date).days) <= window
        ]
        if dupes:
            return _check(
                "no_duplicate_claim",
                label,
                CheckStatus.FAIL,
                f"Overlaps with existing claim(s): {', '.join(dupes)}.",
                claim_ids=dupes,
            )
        return _check("no_duplicate_claim", label, CheckStatus.PASS, "No overlapping claim on this policy.")

    def _no_reused_photo(self, ctx: ClaimContext) -> CheckResult:
        label = "Photos are original to this claim"
        if not ctx.claim.photos:
            return _check("no_reused_photo", label, CheckStatus.UNKNOWN, "No photos submitted.")
        seen = [
            (other.claim_id, p)
            for other in ctx.other_claims
            if other.claim_id != ctx.claim.claim_id
            for p in other.photos
        ]
        matches = []
        for photo in ctx.claim.photos:
            for other_id, other in seen:
                if photo.sha256 == other.sha256:
                    matches.append({"photo_id": photo.photo_id, "claim_id": other_id, "distance": 0})
                elif photo.phash and other.phash:
                    distance = imagehash.hex_to_hash(photo.phash) - imagehash.hex_to_hash(other.phash)
                    if distance <= self.terms.reused_photo_max_distance:
                        matches.append(
                            {"photo_id": photo.photo_id, "claim_id": other_id, "distance": int(distance)}
                        )
        if matches:
            return _check(
                "no_reused_photo",
                label,
                CheckStatus.FAIL,
                f"{len(matches)} photo(s) match photos from other claims.",
                matches=matches,
            )
        return _check("no_reused_photo", label, CheckStatus.PASS, "No photo matches any other claim.")

    def _documents_match_records(self, ctx: ClaimContext) -> CheckResult:
        label = "Uploaded documents match official records"
        extractions = [d.extraction for d in ctx.claim.documents if d.extraction is not None]
        if not extractions:
            return _check(
                "documents_match_records", label, CheckStatus.UNKNOWN, "No documents were read yet."
            )
        mismatches: list[str] = []
        unsure: list[str] = []
        for ex in extractions:
            for field_name, expected in self._expected_fields(ctx, ex).items():
                got = ex.fields.get(field_name)
                if got is None or got.value is None:
                    unsure.append(f"{ex.kind}.{field_name} unreadable")
                elif got.confidence < self.terms.min_extraction_confidence:
                    unsure.append(f"{ex.kind}.{field_name} low confidence ({got.confidence:.2f})")
                elif not self._field_matches(field_name, got.value, expected):
                    mismatches.append(f"{ex.kind}.{field_name}: read '{got.value}', expected '{expected}'")
        if mismatches:
            return _check(
                "documents_match_records",
                label,
                CheckStatus.FAIL,
                "; ".join(mismatches),
                mismatches=mismatches,
                unsure=unsure,
            )
        if unsure:
            return _check(
                "documents_match_records",
                label,
                CheckStatus.UNKNOWN,
                "Needs a human look: " + "; ".join(unsure),
                unsure=unsure,
            )
        return _check(
            "documents_match_records",
            label,
            CheckStatus.PASS,
            f"{len(extractions)} document(s) agree with the land register and bank records.",
        )

    def _expected_fields(self, ctx: ClaimContext, ex: DocumentExtraction) -> dict[str, str]:
        if ex.kind == "land_record":
            expected = {"khasra_no": ctx.policy.plot.khasra_no}
            if ctx.land_record:
                expected["owner_name"] = ctx.land_record.owner_name_hi
            return expected
        if ex.kind == "bank_passbook":
            return {"ifsc": ctx.farmer.bank.ifsc, "account_last4": ctx.farmer.bank.account_masked[-4:]}
        if ex.kind == "policy":
            return {"policy_no": ctx.policy.policy_no}
        return {}

    def _field_matches(self, field_name: str, got: str, expected: str) -> bool:
        if field_name == "ifsc":
            value = _normalise(got).upper()
            return bool(IFSC_PATTERN.match(value)) and value == expected.upper()
        if field_name == "account_last4":
            return re.sub(r"\D", "", got)[-4:] == expected
        if field_name == "owner_name":
            ratio = difflib.SequenceMatcher(None, _normalise(got), _normalise(expected)).ratio()
            return ratio >= self.terms.name_match_ratio
        return _normalise(got) == _normalise(expected)

    # --- Payout -------------------------------------------------------------------

    def payout_quote(self, ctx: ClaimContext, evidence: list[EvidenceItem]) -> PayoutQuote:
        rain = _metric(evidence, "weather", "max_24h_mm")
        flooded = _metric(evidence, "satellite", "flooded_fraction")
        rain_pct, rain_slab = slab_percent(rain, self.terms.excess_rain_slabs_mm_24h)
        flood_pct, flood_slab = slab_percent(flooded, self.terms.flood_slabs_fraction)

        peril = ctx.claim.peril
        if peril == Peril.HAILSTORM:
            percent = self.terms.hailstorm_flat_percent
            basis = f"Hailstorm cover pays a flat {percent:g}% of sum insured once the event is verified."
        elif peril == Peril.EXCESS_RAIN:
            percent = rain_pct
            basis = (
                f"24-hour rainfall of {rain:.0f} mm meets the {rain_slab.at_or_above:g} mm trigger."
                if rain_slab
                else "Rainfall did not reach the 100 mm / 24 h trigger."
                if rain is not None
                else "Rainfall data unavailable; no trigger could be evaluated."
            )
        else:
            percent = max(rain_pct, flood_pct)
            if flood_slab and flood_pct >= rain_pct:
                basis = (
                    f"Radar shows {flooded:.0%} of the area under water, meeting the "
                    f"{flood_slab.at_or_above:.0%} trigger."
                )
            elif rain_slab:
                basis = f"24-hour rainfall of {rain:.0f} mm meets the {rain_slab.at_or_above:g} mm trigger."
            else:
                basis = "Neither the radar flood trigger nor the rainfall trigger was met."

        sum_insured = ctx.policy.sum_insured_inr
        return PayoutQuote(
            sum_insured_inr=sum_insured,
            payout_percent=percent,
            amount_inr=round(sum_insured * percent / 100),
            basis=basis,
        )

    # --- Guidance for the AI scorer -------------------------------------------------

    def scoring_guidance(self, peril: Peril) -> str:
        common = (
            "Hard checks are deterministic rules; treat any failed check as a serious red flag. "
            "Weather, satellite and news are independent of the farmer; photos come from the farmer. "
            "Never invent evidence that is not in the input."
        )
        specific = {
            Peril.FLOOD: (
                "Riverine floods are often caused by rain far upstream, so modest local rainfall does "
                "not contradict a flood. Radar showing standing water near the plot after the loss date "
                "is strong support. Clear radar within ~3 days after the loss date showing no water is "
                "strong contrary evidence. Credible news of flooding in the same block or district on "
                "those dates is strong support."
            ),
            Peril.EXCESS_RAIN: (
                "Gridded rainfall of 100 mm or more in 24 hours at the plot is strong support; "
                "under 20 mm across the event window strongly contradicts the claim. Waterlogging in "
                "radar and local news of heavy rain add support."
            ),
            Peril.HAILSTORM: (
                "Hail is very local and rainfall grids do not measure it, so low rainfall is not "
                "contrary evidence. Thunderstorm activity (WMO weather codes 95-99), strong gusts and "
                "credible local news of hail in the same block or district on that date are strong "
                "support. Photos should show shredded leaves, broken or lodged stems, or hail marks "
                "consistent with the crop and season."
            ),
        }
        return f"{common} {specific[peril]}"
