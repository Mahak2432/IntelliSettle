"""Generate synthetic Bihar land records (Khatiyan) and bank passbooks for the demo farmers.

Renders HTML with headless Microsoft Edge (correct Devanagari shaping), then ages the
image so it looks like a phone photo of a worn paper document. All data is fictional.

Run from the repo root:  python -m uv run --project api python scripts/make_demo_documents.py
"""

from __future__ import annotations

import json
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed"
OUT = ROOT / "web" / "public" / "demo"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

# Fictional account numbers whose last four digits match the masked numbers in farmers.json.
ACCOUNTS = {"F-101": "37120094821", "F-102": "60451107310", "F-103": "41230012056", "F-104": "33900049174"}
HANDWRITTEN = {"F-103", "F-104"}
THANA = {"Kiratpur": "112", "Sikti": "47", "Forbesganj": "63"}

FONTS = """
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=Tiro+Devanagari+Hindi&display=swap" rel="stylesheet">
"""

BASE_CSS = """
body { margin: 0; background: #fbf6e6; font-family: 'Tiro Devanagari Hindi', 'Nirmala UI', serif; color: #1a1a1a; }
.page { width: 860px; padding: 36px 40px; box-sizing: border-box; }
.hand { font-family: 'Kalam', 'Nirmala UI', cursive; color: #1d2a6b; font-size: 1.15em; }
table { width: 100%; border-collapse: collapse; margin-top: 14px; }
td, th { border: 1.5px solid #333; padding: 9px 10px; vertical-align: top; text-align: left; }
th { background: #efe6c8; font-weight: 600; }
.center { text-align: center; }
.stamp { display: inline-block; border: 3px solid #7b2b8f; color: #7b2b8f; border-radius: 50%;
         width: 120px; height: 120px; text-align: center; font-size: 13px; line-height: 1.2;
         padding-top: 34px; box-sizing: border-box; transform: rotate(-14deg); opacity: .75; }
"""


def khatiyan_html(farmer: dict, policy: dict, record: dict) -> str:
    plot = policy["plot"]
    hand = "hand" if farmer["farmer_id"] in HANDWRITTEN else ""
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8">{FONTS}<style>{BASE_CSS}</style></head>
<body><div class="page">
  <div class="center" style="font-size:15px;color:#7b2b8f">नमूना दस्तावेज़. केवल डेमो हेतु. सरकारी अभिलेख नहीं।</div>
  <h1 class="center" style="font-size:28px;margin:10px 0 4px">खतियान (भूमि अभिलेख)</h1>
  <table>
    <tr><th>ज़िला</th><td class="{hand}">{plot['district']}</td><th>अंचल</th><td class="{hand}">{plot['block']}</td></tr>
    <tr><th>मौजा</th><td class="{hand}">{plot['village']}</td><th>थाना संख्या</th><td class="{hand}">{THANA[plot['block']]}</td></tr>
    <tr><th>खाता संख्या</th><td class="{hand}">{int(plot['khasra_no']) // 7 + 31}</td><th>खेसरा संख्या</th><td class="{hand}" style="font-size:1.3em"><b>{plot['khasra_no']}</b></td></tr>
  </table>
  <table>
    <tr><th style="width:34%">रैयत का नाम</th><td class="{hand}" style="font-size:1.25em">{record['owner_name_hi']}</td></tr>
    <tr><th>पिता का नाम</th><td class="{hand}">{farmer['father_name']}</td></tr>
    <tr><th>रकबा (हेक्टेयर)</th><td class="{hand}">{record['area_ha']}</td></tr>
    <tr><th>भूमि की किस्म</th><td class="{hand}">धनहर (सिंचित)</td></tr>
    <tr><th>लगान</th><td class="{hand}">₹ {round(record['area_ha'] * 42)} वार्षिक</td></tr>
  </table>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:34px">
    <div style="font-size:14px">प्रमाणित किया जाता है कि उपरोक्त प्रविष्टि<br>अभिलेख के अनुसार सही है।</div>
    <div class="stamp">नमूना<br>SAMPLE</div>
    <div class="center" style="font-size:14px"><span class="hand" style="font-size:22px">अ. कुमार</span><br>हस्ताक्षर</div>
  </div>
</div></body></html>"""


def passbook_html(farmer: dict, policy: dict) -> str:
    bank = farmer["bank"]
    hand = "hand" if farmer["farmer_id"] in HANDWRITTEN else ""
    acct = ACCOUNTS[farmer["farmer_id"]]
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8">{FONTS}<style>{BASE_CSS}
  body {{ background: #eef3f7; }}
  .page {{ font-family: 'Nirmala UI', sans-serif; }}
  .bank {{ background: #12395f; color: #fff; padding: 16px 22px; font-size: 26px; font-weight: 700; border-radius: 6px; }}
  .row {{ display:flex; border-bottom: 1px dashed #8aa; padding: 11px 0; font-size: 19px; }}
  .row b {{ width: 230px; font-weight: 600; color: #234; }}
</style></head>
<body><div class="page">
  <div class="bank">{bank['bank_name']}<div style="font-size:15px;font-weight:400">बचत खाता पासबुक / Savings Account Passbook</div></div>
  <div style="display:flex;gap:26px;margin-top:22px">
    <div style="flex:1">
      <div class="row"><b>खाताधारक / Name</b><span class="{hand}">{farmer['name_hi']} ({farmer['name']})</span></div>
      <div class="row"><b>पिता / Father</b><span class="{hand}">{farmer['father_name']}</span></div>
      <div class="row"><b>खाता सं. / A/c No.</b><span class="{hand}" style="letter-spacing:2px">{acct}</span></div>
      <div class="row"><b>IFSC</b><span class="{hand}" style="letter-spacing:2px">{bank['ifsc']}</span></div>
      <div class="row"><b>शाखा / Branch</b><span class="{hand}">{policy['plot']['block']}, {policy['plot']['district']}</span></div>
      <div class="row"><b>CIF</b><span class="{hand}">8{acct[-6:]}{acct[:3]}</span></div>
    </div>
    <div style="width:150px;height:180px;border:2px solid #789;display:grid;place-items:center;color:#789;font-size:14px">फ़ोटो</div>
  </div>
  <div style="margin-top:22px;font-size:13px;color:#456">नमूना दस्तावेज़. केवल डेमो हेतु. Sample document for demo only.</div>
</div></body></html>"""


def render(html: str, out_png: Path, height: int) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "doc.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--virtual-time-budget=6000", f"--window-size=860,{height}",
                f"--screenshot={out_png}", page.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=90,
        )


def age(png: Path, seed: int) -> Image.Image:
    """Make a clean render look like a phone photo of worn paper."""
    rng = random.Random(seed)
    doc = Image.open(png).convert("RGB")
    doc = ImageEnhance.Color(doc).enhance(0.85)
    tint = Image.new("RGB", doc.size, (232, 214, 170))
    doc = Image.blend(doc, tint, 0.12)
    noise = Image.effect_noise(doc.size, 22).convert("RGB")
    doc = Image.blend(doc, noise, 0.06)
    background = Image.new("RGB", (doc.width + 160, doc.height + 160), (92, 70, 52))
    background.paste(doc, (80, 80))
    rotated = background.rotate(rng.uniform(-3.5, 3.5), resample=Image.BICUBIC, expand=False, fillcolor=(92, 70, 52))
    shaded = ImageEnhance.Brightness(rotated).enhance(rng.uniform(0.86, 0.97))
    shaded = shaded.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.1)))
    return ImageOps.fit(shaded, (1000, int(1000 * shaded.height / shaded.width)))


def main() -> None:
    farmers = {f["farmer_id"]: f for f in json.loads((SEED / "farmers.json").read_text(encoding="utf-8"))}
    policies = {p["farmer_id"]: p for p in json.loads((SEED / "policies.json").read_text(encoding="utf-8"))}
    records = {r["owner_farmer_id"]: r for r in json.loads((SEED / "land_records.json").read_text(encoding="utf-8"))}

    for i, (fid, farmer) in enumerate(farmers.items()):
        folder = OUT / fid
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            for name, html, height in (
                ("khatiyan", khatiyan_html(farmer, policies[fid], records[fid]), 900),
                ("passbook", passbook_html(farmer, policies[fid]), 560),
            ):
                png = Path(tmp) / f"{name}.png"
                render(html, png, height)
                age(png, seed=i * 10 + len(name)).save(folder / f"{name}.jpg", quality=72)

        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"photos": []}
        manifest |= {"land_record": "khatiyan.jpg", "bank_passbook": "passbook.jpg"}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"{fid}: documents written to {folder}")


if __name__ == "__main__":
    main()
