"""Deploy web/out to Firebase Hosting through the Hosting REST API, using gcloud credentials.

Equivalent to `firebase deploy --only hosting`, but needs no separate Firebase CLI login.
Run from the repo root:  python -m uv run --project api python scripts/deploy_hosting.py
"""

from __future__ import annotations

import gzip
import hashlib
import sys
from pathlib import Path

import google.auth
import google.auth.transport.requests
import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "out"
PROJECT = "insurance-crisis"
SITE = "insurance-crisis"
API = "https://firebasehosting.googleapis.com/v1beta1"
CONFIG = {
    "trailingSlashBehavior": "ADD",
    "headers": [
        {"glob": "/_next/static/**", "headers": {"Cache-Control": "public, max-age=31536000, immutable"}}
    ],
}


def gz(data: bytes) -> bytes:
    return gzip.compress(data, mtime=0)


def main() -> None:
    if not (OUT / "index.html").exists():
        sys.exit("web/out is missing. Run `npm run build` in web/ first.")
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {"Authorization": f"Bearer {credentials.token}", "x-goog-user-project": PROJECT}

    files: dict[str, bytes] = {}
    for path in OUT.rglob("*"):
        if path.is_file():
            files["/" + path.relative_to(OUT).as_posix()] = gz(path.read_bytes())
    hashes = {name: hashlib.sha256(blob).hexdigest() for name, blob in files.items()}
    by_hash = {hashes[name]: blob for name, blob in files.items()}

    with httpx.Client(headers=headers, timeout=120) as client:
        version = client.post(f"{API}/sites/{SITE}/versions", json={"config": CONFIG})
        version.raise_for_status()
        name = version.json()["name"]

        populate = client.post(f"{API}/{name}:populateFiles", json={"files": hashes})
        populate.raise_for_status()
        body = populate.json()
        required = body.get("uploadRequiredHashes", [])
        for digest in required:
            upload = client.post(
                f"{body['uploadUrl']}/{digest}",
                content=by_hash[digest],
                headers={"Content-Type": "application/octet-stream"},
            )
            upload.raise_for_status()

        client.patch(f"{API}/{name}", params={"update_mask": "status"}, json={"status": "FINALIZED"}).raise_for_status()
        release = client.post(f"{API}/sites/{SITE}/releases", params={"versionName": name})
        release.raise_for_status()

    print(f"Uploaded {len(required)} of {len(files)} files. Live at https://{SITE}.web.app")


if __name__ == "__main__":
    main()
