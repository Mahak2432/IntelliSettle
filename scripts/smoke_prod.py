"""End-to-end smoke test against the deployed API, signing in the same way the web app does.

Run from the repo root:  python -m uv run --project api python scripts/smoke_prod.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API = "https://intellisettle-api-929855157031.asia-south1.run.app"


def _web_env(name: str) -> str:
    """Read a value from the web app's production env file, which stays out of git."""
    path = ROOT / "web" / ".env.production.local"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return next((ln.split("=", 1)[1].strip() for ln in lines if ln.startswith(name + "=")), "")


# The Firebase web API key is public by design (it ships in the site), but is kept out of the source.
FIREBASE_WEB_KEY = os.environ.get("FIREBASE_WEB_KEY") or _web_env("NEXT_PUBLIC_FIREBASE_API_KEY")
FARMER, POLICY = "F-104", "KK-23K-DBG-0104"
DEMO = ROOT / "web" / "public" / "demo" / FARMER


def anonymous_token() -> str:
    r = httpx.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_KEY}",
        json={"returnSecureToken": True},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["idToken"]


def main() -> None:
    headers = {"Authorization": f"Bearer {anonymous_token()}"}
    with httpx.Client(base_url=API, headers=headers, timeout=120) as api:
        assert api.get("/api/health").json() == {"status": "ok"}
        api.post("/api/session", json={"role": "farmer", "farmer_id": FARMER}).raise_for_status()
        manifest = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))
        files = [("photos", (p, (DEMO / p).read_bytes(), "image/jpeg")) for p in manifest["photos"]]
        files += [(k, (manifest[k], (DEMO / manifest[k]).read_bytes(), "image/jpeg")) for k in ("land_record", "bank_passbook")]
        filed = api.post(
            "/api/claims",
            data={"policy_no": POLICY, "peril": "flood", "loss_date": "2023-10-25", "description": "smoke test"},
            files=files,
        )
        filed.raise_for_status()
        claim_id = filed.json()["claim_id"]
        print("filed", claim_id)

        for _ in range(40):
            status = api.get(f"/api/claims/{claim_id}").json()["status"]
            if status not in ("submitted", "assessing"):
                break
            time.sleep(3)
        print("status", status)

        api.post("/api/session", json={"role": "reviewer"}).raise_for_status()
        detail = api.get(f"/api/claims/{claim_id}").json()["claim"]
        a = detail["assessment"]
        print("verdict", a["verdict"], "score", a["truth"]["score"], "model", a["truth"]["model"])
        print("evidence", {e["source"]: e["signal"] for e in a["evidence"]})
        photo = api.get(f"/api/claims/{claim_id}/files/photos/0")
        print("photo from bucket", photo.status_code, photo.headers.get("content-type"), len(photo.content), "bytes")
        print(claim_id)


if __name__ == "__main__":
    main()
