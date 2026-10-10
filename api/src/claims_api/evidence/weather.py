"""Rainfall at the exact plot from Open-Meteo gridded data (ERA5 reanalysis for older dates).

Gridded data removes the "basis risk" of using a weather station that may be
tens of kilometres from the farm.
"""

from __future__ import annotations

from datetime import date, timedelta

import httpx

from claims_api.domain.context import ClaimContext
from claims_api.domain.models import Citation, EvidenceItem, GeoPoint, Peril, Signal
from claims_api.evidence.base import EvidenceCollector, date_window
from claims_api.infra.replay import Recorder

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
THUNDERSTORM_CODES = {95, 96, 99}
HAIL_CODES = {96, 99}
CONVECTIVE_BURST_MM_PER_HOUR = 10


class WeatherCollector(EvidenceCollector):
    name = "weather"
    label = "Rainfall at the plot (gridded weather data)"

    def __init__(self, recorder: Recorder, today: date | None = None) -> None:
        self.recorder = recorder
        self.today = today

    async def collect(self, ctx: ClaimContext) -> EvidenceItem:
        start, end = date_window(ctx.claim.loss_date, days_before=3, days_after=1)
        data = await fetch_weather(self.recorder, ctx.policy.plot.location, start, end, self.today)
        metrics = summarise(data)
        signal, summary = interpret(ctx.claim.peril, metrics)
        return EvidenceItem(
            source=self.name,
            label=self.label,
            signal=signal,
            summary=summary,
            metrics=metrics,
            citations=[Citation(title="Open-Meteo historical weather (ERA5)", url="https://open-meteo.com/")],
        )


async def fetch_weather(
    recorder: Recorder, loc: GeoPoint, start: date, end: date, today: date | None = None
) -> dict:
    """Hourly + daily rainfall for a point. `today` is the real date, which decides the data source."""
    today = today or date.today()
    # ERA5 reanalysis lags about five days; recent dates come from the forecast archive.
    url = ARCHIVE_URL if (today - end) > timedelta(days=7) else FORECAST_URL
    params = {
        "latitude": round(loc.lat, 4),
        "longitude": round(loc.lon, 4),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": "precipitation,weather_code,wind_gusts_10m",
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
    }

    async def fetch() -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    return await recorder.call("open-meteo", {"url": url, **params}, fetch)


def summarise(data: dict) -> dict:
    hourly = data.get("hourly", {})
    times: list[str] = hourly.get("time", [])
    rain = [v or 0.0 for v in hourly.get("precipitation", [])]
    codes = [c for c in hourly.get("weather_code", []) if c is not None]
    gusts = [g for g in hourly.get("wind_gusts_10m", []) if g is not None]

    max_24h, max_24h_end = 0.0, None
    for i in range(len(rain)):
        window = sum(rain[max(0, i - 23) : i + 1])
        if window > max_24h:
            max_24h, max_24h_end = window, times[i]

    daily = data.get("daily", {})
    daily_mm = {
        day: round(v or 0.0, 1)
        for day, v in zip(daily.get("time", []), daily.get("precipitation_sum", []), strict=False)
    }
    return {
        "max_24h_mm": round(max_24h, 1),
        "max_24h_ending": max_24h_end,
        "window_total_mm": round(sum(rain), 1),
        "max_hourly_mm": round(max(rain), 1) if rain else 0.0,
        "daily_mm": daily_mm,
        "thunderstorm_hours": sum(1 for c in codes if c in THUNDERSTORM_CODES),
        "hail_code_hours": sum(1 for c in codes if c in HAIL_CODES),
        "max_gust_kmh": round(max(gusts), 1) if gusts else None,
        "grid_lat": data.get("latitude"),
        "grid_lon": data.get("longitude"),
    }


def interpret(peril: Peril, m: dict) -> tuple[Signal, str]:
    max24, total = m["max_24h_mm"], m["window_total_mm"]
    rain_text = f"Max 24-hour rainfall {max24:.0f} mm; {total:.0f} mm across the 5-day window."
    if peril == Peril.EXCESS_RAIN:
        if max24 >= 100:
            return Signal.SUPPORTS, f"Extreme rain recorded at the plot. {rain_text}"
        if total < 20:
            return Signal.CONTRADICTS, f"Almost no rain at the plot around the claimed date. {rain_text}"
        return Signal.INCONCLUSIVE, f"Some rain, but below the extreme-rain level. {rain_text}"
    if peril == Peril.FLOOD:
        if max24 >= 100 or total >= 150:
            return Signal.SUPPORTS, f"Heavy local rain consistent with flooding. {rain_text}"
        return (
            Signal.INCONCLUSIVE,
            f"Local rain was modest; river floods can come from rain upstream. {rain_text}",
        )
    storms = m["thunderstorm_hours"]
    burst = m.get("max_hourly_mm", 0.0)
    if storms:
        return Signal.SUPPORTS, f"{storms} hour(s) of thunderstorm activity recorded. {rain_text}"
    # Reanalysis grids never encode hail, but hail falls from intense convective bursts.
    if burst >= CONVECTIVE_BURST_MM_PER_HOUR:
        return (
            Signal.SUPPORTS,
            f"Sudden intense storm (peak {burst:.0f} mm in one hour), the kind that brings hail. "
            f"Grids cannot measure hail itself. {rain_text}",
        )
    return Signal.INCONCLUSIVE, f"No storm burst in the grid data; hail is very local. {rain_text}"
