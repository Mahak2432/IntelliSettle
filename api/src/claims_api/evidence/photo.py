"""Gemini looks at the farmer's damage photos."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, Field

from claims_api.ai.gemini import GeminiClient, ImageInput
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import EvidenceItem, Signal
from claims_api.evidence.base import PERIL_WORDS, EvidenceCollector
from claims_api.infra.storage import BlobStore

MAX_PHOTOS = 4
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

SYSTEM = (
    "You are an agricultural loss assessor in India reviewing photos a farmer submitted with a crop "
    "insurance claim. Describe only what is visible. Be specific and conservative. Flag anything that "
    "suggests the photo is not an original field photo: screenshots, watermarks, stock-photo framing, "
    "signs of editing or AI generation, or scenes that do not match the claimed crop or season."
)


class PhotoAssessment(BaseModel):
    shows_farm_field: bool
    crop_seen: str
    crop_matches_policy: Literal["yes", "no", "unclear"]
    damage_visible: bool
    damage_type: str
    consistent_with_peril: Literal["yes", "no", "unclear"]
    severity_percent: int = Field(ge=0, le=100)
    authenticity_concerns: list[str]
    summary: str


class PhotoCollector(EvidenceCollector):
    name = "photo"
    label = "AI review of the farmer's photos"

    def __init__(self, gemini: GeminiClient, blobs: BlobStore) -> None:
        self.gemini = gemini
        self.blobs = blobs

    async def collect(self, ctx: ClaimContext) -> EvidenceItem:
        photos = ctx.claim.photos[:MAX_PHOTOS]
        if not photos:
            return self.unavailable("No damage photos were submitted.")
        images = [
            ImageInput(
                data=await self.blobs.get(p.storage_path),
                mime_type=MIME.get(PurePosixPath(p.storage_path).suffix.lower(), "image/jpeg"),
            )
            for p in photos
        ]
        prompt = (
            f"Claimed loss: {PERIL_WORDS[ctx.claim.peril]} on {ctx.claim.loss_date:%d %B %Y}. "
            f"Insured crop: {ctx.policy.crop} ({ctx.policy.season}), {ctx.policy.plot.district}, "
            f'{ctx.policy.plot.state}. Farmer\'s description: "{ctx.claim.description}". '
            "Assess the attached photos."
        )
        result = await self.gemini.generate_json(
            namespace="gemini-photo", system=SYSTEM, prompt=prompt, schema=PhotoAssessment, images=images
        )
        return interpret(PhotoAssessment.model_validate(result["data"]), self.label)


def interpret(a: PhotoAssessment, label: str) -> EvidenceItem:
    if a.authenticity_concerns or not a.shows_farm_field or a.consistent_with_peril == "no":
        signal = Signal.CONTRADICTS
    elif a.damage_visible and a.consistent_with_peril == "yes":
        signal = Signal.SUPPORTS
    else:
        signal = Signal.INCONCLUSIVE
    return EvidenceItem(
        source="photo",
        label=label,
        signal=signal,
        summary=a.summary,
        metrics=a.model_dump(),
        independent=False,
    )
