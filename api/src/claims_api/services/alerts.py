"""Heavy-rain alerts for a farmer's insured plots.

The system only notifies. It never files a claim on the farmer's behalf.
Categories follow the India Meteorological Department's 24-hour rainfall scale.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta

from pydantic import BaseModel

from claims_api.domain.models import Policy
from claims_api.evidence.weather import fetch_weather
from claims_api.infra.replay import Recorder

log = logging.getLogger(__name__)

IMD_CATEGORIES = (
    (204.5, "extremely heavy rain", "अत्यंत भारी बारिश"),
    (115.6, "very heavy rain", "बहुत भारी बारिश"),
    (64.5, "heavy rain", "भारी बारिश"),
)
LOOKBACK_DAYS = 3
CACHE_SECONDS = 3600


class RainAlert(BaseModel):
    policy_no: str
    date: date
    rain_mm: float
    category_en: str
    category_hi: str


def categorise(mm: float) -> tuple[str, str] | None:
    for threshold, en, hi in IMD_CATEGORIES:
        if mm >= threshold:
            return en, hi
    return None


class RainAlertService:
    def __init__(self, recorder: Recorder) -> None:
        self.recorder = recorder
        self._cache: dict[tuple[str, date], tuple[float, RainAlert | None]] = {}

    async def alerts_for(self, policies: list[Policy], today: date) -> list[RainAlert]:
        alerts = []
        for policy in policies:
            if not policy.cover_start <= today <= policy.cover_end + timedelta(days=LOOKBACK_DAYS):
                continue
            alert = await self._check(policy, today)
            if alert:
                alerts.append(alert)
        return alerts

    async def _check(self, policy: Policy, today: date) -> RainAlert | None:
        key = (policy.policy_no, today)
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
            return cached[1]
        try:
            data = await fetch_weather(
                self.recorder, policy.plot.location, today - timedelta(days=LOOKBACK_DAYS), today
            )
        except Exception:
            log.exception("Rain alert check failed for %s", policy.policy_no)
            return None
        daily = data.get("daily", {})
        alert = None
        for day, mm in sorted(zip(daily.get("time", []), daily.get("precipitation_sum", []), strict=False)):
            category = categorise(mm or 0.0)
            if category:
                alert = RainAlert(
                    policy_no=policy.policy_no,
                    date=date.fromisoformat(day),
                    rain_mm=round(mm, 1),
                    category_en=category[0],
                    category_hi=category[1],
                )
        self._cache[key] = (time.monotonic(), alert)
        return alert
