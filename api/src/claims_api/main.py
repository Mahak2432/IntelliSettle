from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from claims_api.api.auth import Identity, farmer_session, identity, reviewer_session, session
from claims_api.api.views import FarmerClaimView, ReviewClaimView, ReviewQueueItem
from claims_api.config import get_settings
from claims_api.container import Container, get_container
from claims_api.domain.models import Claim, ClaimStatus, GeoPoint, Language, Peril, ReviewThresholds
from claims_api.domain.time import IST
from claims_api.services.claims import ClaimError, NewDocument, NewPhoto
from claims_api.services.sessions import Role, Session

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("claims_api")

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Crop Claims API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ClaimError)
async def claim_error(_: Request, exc: ClaimError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# --- Session ----------------------------------------------------------------------


@app.delete("/api/demo/claims")
async def reset_demo(s: Session = Depends(session), c: Container = Depends(get_container)) -> dict:
    """Start the demo over: removes only the claims this browser session filed."""
    if not c.settings.demo_sandbox:
        raise HTTPException(403, "Resetting is only available in demo mode.")
    mine = await c.claims.repo.list(sandbox=s.uid)
    for claim in mine:
        await c.claims.repo.delete(claim.claim_id)
    return {"removed": len(mine)}


@app.get("/api/demo/personas")
async def personas(c: Container = Depends(get_container)) -> list[dict]:
    path = c.settings.seed_dir / "personas.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


class SessionRequest(BaseModel):
    role: Role
    farmer_id: str | None = None


@app.post("/api/session")
async def start_session(
    body: SessionRequest, who: Identity = Depends(identity), c: Container = Depends(get_container)
) -> Session:
    if body.role == "farmer" and (not body.farmer_id or not c.reference.farmer(body.farmer_id)):
        raise HTTPException(400, "Unknown farmer profile.")
    s = Session(uid=who.uid, role=body.role, farmer_id=body.farmer_id if body.role == "farmer" else None)
    await c.sessions.save(s)
    return s


@app.get("/api/me")
async def me(s: Session = Depends(session), c: Container = Depends(get_container)) -> dict:
    if s.role == "reviewer":
        return {"role": "reviewer"}
    farmer = c.reference.farmer(s.farmer_id)
    policies = c.reference.policies_for(s.farmer_id)
    today = c.claims.now_for(s.farmer_id).astimezone(IST).date()
    alerts = await c.alerts.alerts_for(policies, today) if c.alerts else []
    return {"role": "farmer", "farmer": farmer, "policies": policies, "alerts": alerts}


# --- Claims -----------------------------------------------------------------------


async def _read_image(upload: UploadFile) -> bytes:
    if upload.content_type not in IMAGE_TYPES:
        raise ClaimError("Only JPEG, PNG or WebP photos are accepted.")
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ClaimError("Each photo must be under 8 MB.")
    return data


async def _assess_in_background(c: Container, claim_id: str) -> None:
    try:
        await c.claims.assess(claim_id)
    except Exception:
        log.exception("Assessment failed for claim %s", claim_id)


@app.post("/api/claims", status_code=201)
async def submit_claim(
    background: BackgroundTasks,
    policy_no: str = Form(...),
    peril: Peril = Form(...),
    loss_date: date = Form(...),
    description: str = Form("", max_length=2000),
    language: Language = Form("hi"),
    filed_lat: float | None = Form(None),
    filed_lon: float | None = Form(None),
    photo_meta: str = Form("[]"),
    photos: list[UploadFile] = File(...),
    land_record: UploadFile | None = File(None),
    bank_passbook: UploadFile | None = File(None),
    s: Session = Depends(farmer_session),
    c: Container = Depends(get_container),
) -> FarmerClaimView:
    if len(photos) > 6:
        raise ClaimError("Up to 6 photos per claim.")
    try:
        meta = json.loads(photo_meta)
    except json.JSONDecodeError:
        raise ClaimError("photo_meta must be a JSON list.") from None

    new_photos = []
    for i, upload in enumerate(photos):
        m = meta[i] if i < len(meta) and isinstance(meta[i], dict) else {}
        new_photos.append(
            NewPhoto(
                data=await _read_image(upload),
                content_type=upload.content_type,
                device_captured_at=datetime.fromisoformat(m["captured_at"]) if m.get("captured_at") else None,
                device_location=GeoPoint(lat=m["lat"], lon=m["lon"]) if m.get("lat") is not None else None,
            )
        )
    docs = [
        NewDocument(kind=kind, data=await _read_image(upload), content_type=upload.content_type)
        for kind, upload in (("land_record", land_record), ("bank_passbook", bank_passbook))
        if upload is not None
    ]
    claim = await c.claims.submit(
        farmer_id=s.farmer_id,
        policy_no=policy_no,
        peril=peril,
        loss_date=loss_date,
        description=description,
        language=language,
        filed_from=GeoPoint(lat=filed_lat, lon=filed_lon) if filed_lat is not None else None,
        photos=new_photos,
        documents=docs,
        sandbox=_sandbox(s, c),
    )
    background.add_task(_assess_in_background, c, claim.claim_id)
    return FarmerClaimView.of(claim)


def _sandbox(s: Session, c: Container) -> str | None:
    """In demo mode each browser session is its own sandbox; otherwise everything is shared."""
    return s.uid if c.settings.demo_sandbox else None


async def _claim_for(claim_id: str, s: Session, c: Container) -> Claim:
    claim = await c.claims.repo.get(claim_id)
    if (
        claim is None
        or claim.sandbox != _sandbox(s, c)
        or (s.role == "farmer" and claim.farmer_id != s.farmer_id)
    ):
        raise HTTPException(404, "Claim not found.")
    return claim


@app.get("/api/claims")
async def list_claims(
    status: list[ClaimStatus] | None = None,
    s: Session = Depends(session),
    c: Container = Depends(get_container),
) -> list[FarmerClaimView] | list[ReviewQueueItem]:
    if s.role == "farmer":
        mine = await c.claims.repo.list(farmer_id=s.farmer_id, sandbox=_sandbox(s, c))
        return [FarmerClaimView.of(x) for x in mine]
    claims = await c.claims.repo.list(statuses=set(status) if status else None, sandbox=_sandbox(s, c))
    return [
        ReviewQueueItem.of(x, c.reference.farmer(x.farmer_id), c.reference.policy(x.policy_no))
        for x in claims
    ]


@app.get("/api/claims/{claim_id}")
async def get_claim(
    claim_id: str, s: Session = Depends(session), c: Container = Depends(get_container)
) -> FarmerClaimView | ReviewClaimView:
    claim = await _claim_for(claim_id, s, c)
    if s.role == "farmer":
        return FarmerClaimView.of(claim)
    return ReviewClaimView(
        claim=claim, farmer=c.reference.farmer(claim.farmer_id), policy=c.reference.policy(claim.policy_no)
    )


@app.get("/api/claims/{claim_id}/files/{kind}/{index}")
async def claim_file(
    claim_id: str,
    kind: Literal["photos", "documents"],
    index: int,
    s: Session = Depends(session),
    c: Container = Depends(get_container),
) -> Response:
    claim = await _claim_for(claim_id, s, c)
    items = claim.photos if kind == "photos" else claim.documents
    if not 0 <= index < len(items):
        raise HTTPException(404, "File not found.")
    path = items[index].storage_path
    media = "image/png" if path.endswith(".png") else "image/webp" if path.endswith(".webp") else "image/jpeg"
    return Response(
        await c.blobs.get(path), media_type=media, headers={"Cache-Control": "private, max-age=3600"}
    )


class AppealRequest(BaseModel):
    message: str = Field(max_length=2000)


@app.post("/api/claims/{claim_id}/appeal")
async def appeal(
    claim_id: str,
    body: AppealRequest,
    s: Session = Depends(farmer_session),
    c: Container = Depends(get_container),
) -> FarmerClaimView:
    await _claim_for(claim_id, s, c)
    return FarmerClaimView.of(await c.claims.appeal(claim_id, s.farmer_id, body.message))


class DecisionRequest(BaseModel):
    action: Literal["approve", "reject"]
    fast_lane: bool = False
    reason: str | None = Field(default=None, max_length=2000)


@app.post("/api/claims/{claim_id}/decision")
async def decide(
    claim_id: str,
    body: DecisionRequest,
    s: Session = Depends(reviewer_session),
    c: Container = Depends(get_container),
) -> ReviewClaimView:
    await _claim_for(claim_id, s, c)
    claim = await c.claims.decide(
        claim_id, action=body.action, fast_lane=body.fast_lane, reason=body.reason, reviewer_id=s.uid
    )
    return ReviewClaimView(
        claim=claim, farmer=c.reference.farmer(claim.farmer_id), policy=c.reference.policy(claim.policy_no)
    )


@app.post("/api/claims/{claim_id}/reassess", status_code=202)
async def reassess(
    claim_id: str,
    background: BackgroundTasks,
    s: Session = Depends(reviewer_session),
    c: Container = Depends(get_container),
) -> dict:
    claim = await _claim_for(claim_id, s, c)
    if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.ASSESSING, ClaimStatus.READY_FOR_REVIEW):
        raise ClaimError("Only undecided claims can be re-checked.")
    background.add_task(_assess_in_background, c, claim_id)
    return {"status": "queued"}


# --- Reviewer settings --------------------------------------------------------------


@app.get("/api/review/thresholds")
async def get_thresholds(
    _: Session = Depends(reviewer_session), c: Container = Depends(get_container)
) -> ReviewThresholds:
    return await c.claims.thresholds.get()


@app.put("/api/review/thresholds")
async def put_thresholds(
    body: ReviewThresholds, _: Session = Depends(reviewer_session), c: Container = Depends(get_container)
) -> ReviewThresholds:
    if body.suspicious_at_or_below >= body.genuine_at_or_above:
        raise ClaimError("The suspicious bar must be below the genuine bar.")
    await c.claims.thresholds.save(body)
    return body
