"""Read photos of handwritten / vernacular documents into structured fields."""

from __future__ import annotations

import re

from pydantic import BaseModel

from claims_api.ai.gemini import GeminiClient, ImageInput
from claims_api.domain.models import DocumentExtraction, DocumentKind, DocumentUpload, ExtractedField
from claims_api.infra.storage import BlobStore

IFSC = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
UNVERIFIED_CONFIDENCE_CAP = 0.5

SYSTEM = (
    "You read photos of Indian land and banking documents for a crop insurance company. Documents may be "
    "handwritten, in Hindi (Devanagari) or English, skewed, folded or faded. Copy names exactly as written, "
    "keeping Devanagari script. Convert all digits to ASCII 0-9. Give each field an honest confidence from "
    "0 to 1. If a field is missing or unreadable, return null with low confidence. Never guess."
)


class LandRecordFields(BaseModel):
    khasra_no: ExtractedField
    owner_name: ExtractedField
    father_name: ExtractedField
    village: ExtractedField
    district: ExtractedField
    area_ha: ExtractedField


class PassbookFields(BaseModel):
    account_holder: ExtractedField
    account_last4: ExtractedField
    ifsc: ExtractedField
    bank_name: ExtractedField


class PolicyFields(BaseModel):
    policy_no: ExtractedField
    farmer_name: ExtractedField
    crop: ExtractedField
    season: ExtractedField
    sum_insured_inr: ExtractedField


class LandRecordReading(BaseModel):
    language: str
    fields: LandRecordFields


class PassbookReading(BaseModel):
    language: str
    fields: PassbookFields


class PolicyReading(BaseModel):
    language: str
    fields: PolicyFields


SCHEMAS: dict[DocumentKind, tuple[type[BaseModel], str]] = {
    "land_record": (
        LandRecordReading,
        "This is a land record extract (Khatauni / Khatiyan / Jamabandi). Extract the plot (khasra) number, "
        "owner name, father's name, village, district and area in hectares (convert from acres or bigha "
        "only if the unit is written; otherwise copy the number as written).",
    ),
    "bank_passbook": (
        PassbookReading,
        "This is the first page of a bank passbook. Extract the account holder, the last 4 digits of the "
        "account number, the IFSC code and the bank name.",
    ),
    "policy": (
        PolicyReading,
        "This is a crop insurance policy document. Extract the policy number, farmer name, crop, season "
        "and sum insured in rupees.",
    ),
}


class DocumentReader:
    def __init__(self, gemini: GeminiClient, blobs: BlobStore) -> None:
        self.gemini = gemini
        self.blobs = blobs

    async def read(self, document: DocumentUpload) -> DocumentExtraction:
        schema, instructions = SCHEMAS[document.kind]
        image = ImageInput(data=await self.blobs.get(document.storage_path))
        result = await self.gemini.generate_json(
            namespace="gemini-documents", system=SYSTEM, prompt=instructions, schema=schema, images=[image]
        )
        reading = schema.model_validate(result["data"])
        fields = {name: field for name, field in reading.fields}
        return DocumentExtraction(
            kind=document.kind,
            language=reading.language,
            fields=validate_fields(fields),
            model=self.gemini.model,
        )


def validate_fields(fields: dict[str, ExtractedField]) -> dict[str, ExtractedField]:
    """Deterministic format checks so a confident-sounding misread cannot slip through."""
    checked = dict(fields)

    def cap(name: str) -> None:
        f = checked[name]
        checked[name] = ExtractedField(value=f.value, confidence=min(f.confidence, UNVERIFIED_CONFIDENCE_CAP))

    if (f := checked.get("ifsc")) and f.value is not None:
        normalised = re.sub(r"\s", "", f.value).upper()
        checked["ifsc"] = ExtractedField(value=normalised, confidence=f.confidence)
        if not IFSC.match(normalised):
            cap("ifsc")
    if (f := checked.get("account_last4")) and f.value is not None:
        digits = re.sub(r"\D", "", f.value)
        checked["account_last4"] = ExtractedField(value=digits[-4:] or None, confidence=f.confidence)
        if len(digits) < 4:
            cap("account_last4")
    if (f := checked.get("area_ha")) and f.value is not None:
        try:
            float(f.value)
        except ValueError:
            cap("area_ha")
    return checked
