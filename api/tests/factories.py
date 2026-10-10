"""Small builders for test data. Override any field with keyword arguments."""

from __future__ import annotations

import hashlib
import io
import itertools
from datetime import date, datetime, timedelta, timezone

from PIL import Image, ImageDraw

from claims_api.domain.context import ClaimContext
from claims_api.domain.models import (
    BankAccount,
    Claim,
    DocumentExtraction,
    DocumentUpload,
    EvidenceItem,
    ExtractedField,
    Farmer,
    GeoPoint,
    LandRecord,
    Peril,
    Photo,
    Plot,
    Policy,
    Signal,
    SowingRecord,
)
from claims_api.intake.photos import write_exif

IST = timezone(timedelta(hours=5, minutes=30))
PLOT_LOCATION = GeoPoint(lat=26.10000, lon=86.20000)
_ids = itertools.count(1)


def farmer(**kw) -> Farmer:
    data = dict(
        farmer_id="F-001",
        name="Ramesh Yadav",
        name_hi="रमेश यादव",
        father_name="Shyam Yadav",
        phone="+919900000001",
        preferred_language="hi",
        bank=BankAccount(
            account_holder="Ramesh Yadav", account_masked="XXXXXX4821", ifsc="SBIN0001234", bank_name="SBI"
        ),
    )
    return Farmer(**(data | kw))


def plot(**kw) -> Plot:
    data = dict(
        khasra_no="412",
        village="Testpur",
        block="Testblock",
        district="Testdistrict",
        state="Bihar",
        area_ha=0.8,
        location=PLOT_LOCATION,
    )
    return Plot(**(data | kw))


def policy(**kw) -> Policy:
    data = dict(
        policy_no="POL-001",
        product_code="crop-parametric-v1",
        farmer_id="F-001",
        insurer="Demo General Insurance",
        scheme="PMFBY",
        season="Kharif 2024",
        crop="paddy",
        plot=plot(),
        insured_area_ha=0.8,
        sum_insured_inr=48000,
        cover_start=date(2024, 6, 15),
        cover_end=date(2024, 11, 30),
        perils=[Peril.FLOOD, Peril.EXCESS_RAIN, Peril.HAILSTORM],
    )
    return Policy(**(data | kw))


def land_record(**kw) -> LandRecord:
    data = dict(
        khasra_no="412",
        village="Testpur",
        district="Testdistrict",
        owner_farmer_id="F-001",
        owner_name_hi="रमेश यादव",
        area_ha=0.8,
    )
    return LandRecord(**(data | kw))


def sowing_record(**kw) -> SowingRecord:
    return SowingRecord(**(dict(farmer_id="F-001", khasra_no="412", season="Kharif 2024", crop="paddy") | kw))


def photo(**kw) -> Photo:
    n = next(_ids)
    data = dict(
        photo_id=f"P{n}",
        storage_path=f"claims/test/photos/{n}.jpg",
        sha256=hashlib.sha256(f"photo-{n}".encode()).hexdigest(),
        phash=f"{n:016x}",
        device_captured_at=datetime(2024, 9, 30, 9, 0, tzinfo=IST),
        device_location=GeoPoint(lat=PLOT_LOCATION.lat + 0.002, lon=PLOT_LOCATION.lon),
    )
    return Photo(**(data | kw))


def extraction(kind: str, confidence: float = 0.95, **values) -> DocumentExtraction:
    defaults = {
        "land_record": {"khasra_no": "412", "owner_name": "रमेश यादव"},
        "bank_passbook": {"ifsc": "SBIN0001234", "account_last4": "4821"},
    }[kind]
    fields = {k: ExtractedField(value=v, confidence=confidence) for k, v in (defaults | values).items()}
    return DocumentExtraction(kind=kind, fields=fields, model="test")


def documents(**overrides) -> list[DocumentUpload]:
    return [
        DocumentUpload(
            document_id="D1",
            kind="land_record",
            storage_path="d1.jpg",
            extraction=overrides.get("land_record", extraction("land_record")),
        ),
        DocumentUpload(
            document_id="D2",
            kind="bank_passbook",
            storage_path="d2.jpg",
            extraction=overrides.get("bank_passbook", extraction("bank_passbook")),
        ),
    ]


def claim(**kw) -> Claim:
    data = dict(
        claim_id=f"CLM-{next(_ids)}",
        policy_no="POL-001",
        farmer_id="F-001",
        product_code="crop-parametric-v1",
        peril=Peril.FLOOD,
        loss_date=date(2024, 9, 29),
        submitted_at=datetime(2024, 9, 30, 10, 0, tzinfo=IST),
        description="खेत में पानी भर गया है, धान की फसल डूब गई।",
        photos=[photo()],
        documents=documents(),
    )
    return Claim(**(data | kw))


def context(**kw) -> ClaimContext:
    data = dict(
        claim=claim(),
        policy=policy(),
        farmer=farmer(),
        land_record=land_record(),
        sowing_record=sowing_record(),
        other_claims=[],
    )
    return ClaimContext(**(data | kw))


def evidence(source: str, signal: Signal, independent: bool = True, **metrics) -> EvidenceItem:
    return EvidenceItem(
        source=source,
        label=source,
        signal=signal,
        summary=f"{source} {signal}",
        metrics=metrics,
        independent=independent,
    )


def jpeg(captured_at: datetime | None = None, location: GeoPoint | None = None, seed: int = 0) -> bytes:
    """A small, unique JPEG with optional EXIF time and GPS."""
    image = Image.new("RGB", (96, 96), (30 + seed * 7 % 200, 110, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle((seed % 60, 10, seed % 60 + 30, 50), fill=(200, 180, 60))
    draw.ellipse((50, (seed * 13) % 50, 90, (seed * 13) % 50 + 40), fill=(20, 60, 160))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return write_exif(buf.getvalue(), captured_at, location)
