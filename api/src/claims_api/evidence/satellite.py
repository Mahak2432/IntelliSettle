"""Standing-water detection from Sentinel-1 radar via Google Earth Engine.

Radar sees through monsoon cloud, which blinds optical satellites exactly when
floods happen. Calm water reflects the radar pulse away from the satellite, so
flooded ground shows up as very low backscatter. Flooded paddy measured about
-16 to -17 dB VV in the 2024 Kosi breach, against -5 to -11 dB for dry fields.
"""

from __future__ import annotations

import asyncio
import base64
from datetime import UTC, date, datetime, timedelta

import httpx

from claims_api.config import Settings
from claims_api.domain.context import ClaimContext
from claims_api.domain.models import Citation, EvidenceItem, Signal
from claims_api.evidence.base import EvidenceCollector
from claims_api.infra.replay import Recorder

WATER_DB = -15
AOI_RADIUS_M = 500
VIEW_RADIUS_M = 2000
# Baseline: passes from 45 days before up to 2 days before the loss.
PRE_DAYS = (45, 1)
# After: passes from the loss date (never earlier) up to 13 days later (Sentinel-1 revisit is ~12 days).
POST_DAYS = (0, 13)
METHOD_VERSION = 2


class SatelliteCollector(EvidenceCollector):
    name = "satellite"
    label = "Sentinel-1 radar flood check"

    def __init__(self, settings: Settings, recorder: Recorder) -> None:
        self.settings = settings
        self.recorder = recorder
        self._initialised = False

    async def collect(self, ctx: ClaimContext) -> EvidenceItem:
        loc, loss = ctx.policy.plot.location, ctx.claim.loss_date
        request = {
            "lat": round(loc.lat, 5),
            "lon": round(loc.lon, 5),
            "loss_date": loss.isoformat(),
            "method": METHOD_VERSION,
        }

        async def fetch() -> dict:
            await asyncio.to_thread(self._init_ee)
            result = await asyncio.to_thread(_measure, loc.lat, loc.lon, loss)
            result["thumbnails"] = await _download_thumbnails(result.pop("thumb_urls", {}))
            return result

        data = await self.recorder.call("earth-engine-s1", request, fetch)
        return interpret(data, loss)

    def _init_ee(self) -> None:
        if self._initialised:
            return
        import ee
        import google.auth

        credentials, project = google.auth.default(
            scopes=[
                "https://www.googleapis.com/auth/earthengine",
                "https://www.googleapis.com/auth/cloud-platform",
            ]
        )
        ee.Initialize(credentials, project=self.settings.gcp_project or project)
        self._initialised = True


def _measure(lat: float, lon: float, loss: date) -> dict:
    import ee

    point = ee.Geometry.Point([lon, lat])
    aoi = point.buffer(AOI_RADIUS_M)
    view = point.buffer(VIEW_RADIUS_M).bounds()
    radar = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .select("VV")
    )

    def window(days_before: int, days_after: int) -> ee.ImageCollection:
        start = (loss - timedelta(days=days_before)).isoformat()
        end = (loss + timedelta(days=days_after)).isoformat()
        return radar.filterDate(start, end).sort("system:time_start")

    pre = window(PRE_DAYS[0], -PRE_DAYS[1])
    post = window(POST_DAYS[0], POST_DAYS[1])
    pre_ms = pre.aggregate_array("system:time_start").getInfo()
    post_ms = post.aggregate_array("system:time_start").getInfo()
    result: dict = {"pre_dates": _days(pre_ms), "post_dates": _days(post_ms)}
    if not post_ms:
        return result

    post_day = _days(post_ms)[0]
    after = post.filterDate(post_day, (date.fromisoformat(post_day) + timedelta(days=1)).isoformat())
    after_img = after.mosaic().focal_median(30, "circle", "meters")
    water_after = after_img.lt(WATER_DB)
    bands = [water_after.rename("after")]
    if pre_ms:
        before_img = pre.median().focal_median(30, "circle", "meters")
        water_before = before_img.lt(WATER_DB)
        bands += [water_before.rename("before"), water_after.And(water_before.Not()).rename("new")]

    stats = ee.Image.cat(bands).reduceRegion(ee.Reducer.mean(), aoi, 10, maxPixels=1e8).getInfo()
    result.update(
        post_date=post_day,
        flooded_fraction=_round(stats.get("after")),
        baseline_water_fraction=_round(stats.get("before")),
        new_water_fraction=_round(stats.get("new")),
    )

    vis = {"region": view, "dimensions": 320, "format": "png"}
    # A two-colour palette keeps the grey layer RGB so it can be merged with the blue water overlay.
    gray = {"min": -25, "max": 0, "palette": ["000000", "ffffff"]}
    overlay = water_after.selfMask().visualize(palette=["1d4ed8"])
    thumbs = {"after": ee.ImageCollection([after_img.visualize(**gray), overlay]).mosaic().getThumbURL(vis)}
    if pre_ms:
        thumbs["before"] = before_img.visualize(**gray).getThumbURL(vis)
    result["thumb_urls"] = thumbs
    return result


def _days(millis: list[int]) -> list[str]:
    return sorted({datetime.fromtimestamp(ms / 1000, UTC).date().isoformat() for ms in millis})


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 3)


async def _download_thumbnails(urls: dict[str, str]) -> dict[str, str]:
    images = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for key, url in urls.items():
            response = await client.get(url)
            response.raise_for_status()
            images[key] = "data:image/png;base64," + base64.b64encode(response.content).decode()
    return images


def interpret(data: dict, loss: date) -> EvidenceItem:
    label = SatelliteCollector.label
    citation = Citation(
        title="Copernicus Sentinel-1 SAR (Google Earth Engine)",
        url="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD",
    )
    if not data.get("post_dates"):
        return EvidenceItem(
            source="satellite",
            label=label,
            signal=Signal.UNAVAILABLE,
            citations=[citation],
            summary="No Sentinel-1 radar pass over the plot in the two weeks after the loss date.",
            metrics={"pre_dates": data.get("pre_dates", [])},
        )

    flooded = data.get("flooded_fraction") or 0.0
    new = data.get("new_water_fraction")
    post_date = date.fromisoformat(data["post_date"])
    lag = (post_date - loss).days
    metrics = {k: v for k, v in data.items() if k != "thumbnails"} | {"days_after_loss": lag}
    new_text = f" ({new:.0%} newly flooded compared with before)" if new is not None else ""
    pass_text = f"Radar pass on {post_date:%d %b %Y}, {lag} day(s) after the loss"

    if flooded >= 0.10 and (new is None or new >= 0.05):
        signal = Signal.SUPPORTS
        summary = f"{pass_text}, shows {flooded:.0%} of the area around the plot under water{new_text}."
    elif flooded < 0.03 and lag <= 3:
        signal = Signal.CONTRADICTS
        summary = f"{pass_text}, shows no standing water around the plot ({flooded:.0%})."
    else:
        signal = Signal.INCONCLUSIVE
        summary = f"{pass_text}, shows {flooded:.0%} of the area under water{new_text}."
    return EvidenceItem(
        source="satellite",
        label=label,
        signal=signal,
        summary=summary,
        metrics=metrics,
        citations=[citation],
        visuals=data.get("thumbnails", {}),
    )
