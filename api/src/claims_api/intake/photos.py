"""Facts we can read straight from an uploaded photo: fingerprints, EXIF time and GPS."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

import imagehash
from PIL import Image

from claims_api.domain.models import GeoPoint
from claims_api.domain.time import IST

GPS_IFD, EXIF_IFD = 0x8825, 0x8769
DATETIME_ORIGINAL, OFFSET_TIME_ORIGINAL, DATETIME = 36867, 36881, 306


@dataclass(frozen=True)
class PhotoFacts:
    sha256: str
    phash: str
    captured_at: datetime | None
    location: GeoPoint | None


def inspect_photo(data: bytes) -> PhotoFacts:
    image = Image.open(io.BytesIO(data))
    exif = image.getexif()
    return PhotoFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        phash=str(imagehash.phash(image)),
        captured_at=_captured_at(exif),
        location=_location(exif),
    )


def _captured_at(exif: Image.Exif) -> datetime | None:
    sub = exif.get_ifd(EXIF_IFD)
    raw = sub.get(DATETIME_ORIGINAL) or exif.get(DATETIME)
    if not raw:
        return None
    try:
        naive = datetime.strptime(str(raw).strip("\x00"), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    offset = sub.get(OFFSET_TIME_ORIGINAL)
    if offset:
        try:
            return datetime.fromisoformat(f"{naive.isoformat()}{str(offset).strip()}")
        except ValueError:
            pass
    # Phones in India almost always record local time without an offset.
    return naive.replace(tzinfo=IST)


def _location(exif: Image.Exif) -> GeoPoint | None:
    gps = exif.get_ifd(GPS_IFD)
    try:
        lat = _degrees(gps[2], gps[1])
        lon = _degrees(gps[4], gps[3])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return GeoPoint(lat=lat, lon=lon)


def _degrees(dms, ref) -> float:
    d, m, s = (float(x) for x in dms)
    value = d + m / 60 + s / 3600
    return -value if str(ref).upper().startswith(("S", "W")) else value


def write_exif(data: bytes, captured_at: datetime | None, location: GeoPoint | None) -> bytes:
    """Stamp time and GPS into a JPEG. Used to build realistic demo and test photos."""
    image = Image.open(io.BytesIO(data)).convert("RGB")
    exif = Image.Exif()
    if captured_at:
        local = captured_at.astimezone(IST)
        exif[DATETIME] = local.strftime("%Y:%m:%d %H:%M:%S")
        exif.get_ifd(EXIF_IFD).update(
            {DATETIME_ORIGINAL: local.strftime("%Y:%m:%d %H:%M:%S"), OFFSET_TIME_ORIGINAL: "+05:30"}
        )
    if location:
        exif.get_ifd(GPS_IFD).update(
            {
                1: "N" if location.lat >= 0 else "S",
                2: _dms(abs(location.lat)),
                3: "E" if location.lon >= 0 else "W",
                4: _dms(abs(location.lon)),
            }
        )
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=88, exif=exif)
    return out.getvalue()


def _dms(value: float) -> tuple[Fraction, Fraction, Fraction]:
    degrees = int(value)
    minutes_full = (value - degrees) * 60
    minutes = int(minutes_full)
    seconds = Fraction(round((minutes_full - minutes) * 60 * 10000), 10000)
    return Fraction(degrees), Fraction(minutes), seconds
