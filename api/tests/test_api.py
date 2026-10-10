import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from claims_api.config import Settings, get_settings
from claims_api.container import Container, get_container
from claims_api.engine.pipeline import ClaimAssessor
from claims_api.engine.scoring import HeuristicTruthScorer
from claims_api.infra.storage import LocalBlobStore
from claims_api.main import app
from claims_api.services.claims import ClaimService
from claims_api.services.payouts import SimulatedPayoutRail
from claims_api.services.reference import ReferenceData
from claims_api.services.sessions import InMemorySessionStore
from claims_api.store.claims import InMemoryClaimRepository, InMemoryThresholdStore
from tests import factories as f
from tests import stubs

FARMER = {"X-Dev-Uid": "farmer-device"}
OFFICER = {"X-Dev-Uid": "officer-laptop"}


@pytest.fixture
def client(tmp_path):
    settings = Settings(auth_mode="dev", seed_dir=tmp_path / "seed", uploads_dir=tmp_path / "uploads")
    reference = ReferenceData([f.farmer()], [f.policy()], [f.land_record()], [f.sowing_record()])
    heuristic = HeuristicTruthScorer()
    blobs = LocalBlobStore(settings.uploads_dir)
    service = ClaimService(
        repo=InMemoryClaimRepository(),
        reference=reference,
        assessor=ClaimAssessor(
            stubs.genuine_flood_collectors(), heuristic, heuristic, stubs.FixedDocumentReader()
        ),
        blobs=blobs,
        thresholds=InMemoryThresholdStore(),
        payouts=SimulatedPayoutRail(),
        clock=lambda: datetime(2024, 9, 30, 11, 0, tzinfo=f.IST),
    )
    container = Container(settings, reference, blobs, service, InMemorySessionStore(), gemini=None)
    app.dependency_overrides[get_container] = lambda: container
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def file_claim(client: TestClient) -> dict:
    taken = datetime(2024, 9, 30, 8, 0, tzinfo=f.IST)
    meta = [{"captured_at": taken.isoformat(), "lat": f.PLOT_LOCATION.lat, "lon": f.PLOT_LOCATION.lon}]
    response = client.post(
        "/api/claims",
        headers=FARMER,
        data={
            "policy_no": "POL-001",
            "peril": "flood",
            "loss_date": "2024-09-29",
            "description": "पूरा खेत पानी में डूबा है",
            "photo_meta": json.dumps(meta),
        },
        files=[
            ("photos", ("field.jpg", f.jpeg(seed=1), "image/jpeg")),
            ("land_record", ("khatauni.jpg", f.jpeg(seed=2), "image/jpeg")),
            ("bank_passbook", ("passbook.jpg", f.jpeg(seed=3), "image/jpeg")),
        ],
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_full_claim_journey_over_http(client):
    assert client.post(
        "/api/session", headers=FARMER, json={"role": "farmer", "farmer_id": "F-001"}
    ).is_success
    me = client.get("/api/me", headers=FARMER).json()
    assert me["policies"][0]["policy_no"] == "POL-001"

    filed = file_claim(client)
    claim_id = filed["claim_id"]

    farmer_view = client.get(f"/api/claims/{claim_id}", headers=FARMER).json()
    assert farmer_view["status"] == "ready_for_review"
    assert farmer_view["message_hi"]
    assert "assessment" not in farmer_view and "score" not in json.dumps(farmer_view)

    client.post("/api/session", headers=OFFICER, json={"role": "reviewer"})
    queue = client.get("/api/claims", headers=OFFICER).json()
    assert queue[0]["verdict"] == "looks_genuine"
    assert queue[0]["score"] >= 80

    detail = client.get(f"/api/claims/{claim_id}", headers=OFFICER).json()
    assert len(detail["claim"]["assessment"]["checks"]) == 10
    photo = client.get(f"/api/claims/{claim_id}/files/photos/0", headers=OFFICER)
    assert photo.headers["content-type"] == "image/jpeg"

    decided = client.post(
        f"/api/claims/{claim_id}/decision", headers=OFFICER, json={"action": "approve", "fast_lane": True}
    )
    assert decided.json()["claim"]["status"] == "paid"

    final = client.get(f"/api/claims/{claim_id}", headers=FARMER).json()
    assert final["payout"]["amount_inr"] == 24000


def test_farmers_cannot_review_and_need_a_session(client):
    assert client.get("/api/me", headers=FARMER).status_code == 403
    client.post("/api/session", headers=FARMER, json={"role": "farmer", "farmer_id": "F-001"})
    filed = file_claim(client)
    response = client.post(
        f"/api/claims/{filed['claim_id']}/decision",
        headers=FARMER,
        json={"action": "approve", "fast_lane": True},
    )
    assert response.status_code == 403


def test_business_rule_errors_return_400_with_message(client):
    client.post("/api/session", headers=OFFICER, json={"role": "reviewer"})
    response = client.put(
        "/api/review/thresholds",
        headers=OFFICER,
        json={"genuine_at_or_above": 50, "suspicious_at_or_below": 60},
    )
    assert response.status_code == 400
    assert "suspicious bar" in response.json()["detail"]
