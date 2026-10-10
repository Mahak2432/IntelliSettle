"""Turn source damage photos into the demo farmers' "phone photos".

Put source photos in data/source-photos/<farmer_id>/ (JPEG/PNG). For each scenario this
resizes them and stamps EXIF capture time (shortly before the claim is filed) and GPS
(50-150 m from the insured plot), exactly as a phone camera would.

Run from the repo root:  python -m uv run --project api python scripts/stamp_demo_photos.py
"""

from __future__ import annotations

import io
import json
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api" / "src"))

from claims_api.domain.models import GeoPoint  # noqa: E402
from claims_api.intake.photos import write_exif  # noqa: E402

SOURCES = ROOT / "data" / "source-photos"
OUT = ROOT / "web" / "public" / "demo"
MAX_SIDE = 1600


def nearby(point: GeoPoint, rng: random.Random) -> GeoPoint:
    metres, bearing = rng.uniform(50, 150), rng.uniform(0, 2 * math.pi)
    dlat = metres * math.cos(bearing) / 111_320
    dlon = metres * math.sin(bearing) / (111_320 * math.cos(math.radians(point.lat)))
    return GeoPoint(lat=point.lat + dlat, lon=point.lon + dlon)


def main() -> None:
    scenarios = json.loads((ROOT / "data" / "seed" / "scenarios.json").read_text(encoding="utf-8"))
    policies = {p["policy_no"]: p for p in json.loads((ROOT / "data" / "seed" / "policies.json").read_text(encoding="utf-8"))}
    for s in scenarios:
        fid = s["farmer_id"]
        sources = sorted(p for p in (SOURCES / fid).glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        if not sources:
            print(f"{fid}: no source photos in {SOURCES / fid}, skipped")
            continue
        rng = random.Random(fid)
        plot = GeoPoint(**policies[s["policy_no"]]["plot"]["location"])
        filed = datetime.fromisoformat(s["filed_at"])
        folder = OUT / fid
        folder.mkdir(parents=True, exist_ok=True)
        names = []
        for i, src in enumerate(sources, 1):
            image = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            image.thumbnail((MAX_SIDE, MAX_SIDE))
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=90)
            taken = filed - timedelta(minutes=rng.randint(25, 95))
            name = f"damage-{i}.jpg"
            (folder / name).write_bytes(write_exif(buf.getvalue(), taken, nearby(plot, rng)))
            names.append(name)
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        manifest["photos"] = names
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"{fid}: {len(names)} photo(s) stamped")


if __name__ == "__main__":
    main()
