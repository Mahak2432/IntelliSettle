from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import ClassVar

from claims_api.domain.context import ClaimContext
from claims_api.domain.models import EvidenceItem, Peril, Signal

PERIL_WORDS = {
    Peril.FLOOD: "flood or inundation",
    Peril.EXCESS_RAIN: "very heavy or excess rainfall",
    Peril.HAILSTORM: "hailstorm",
}


class EvidenceCollector(ABC):
    name: ClassVar[str]
    label: ClassVar[str]

    @abstractmethod
    async def collect(self, ctx: ClaimContext) -> EvidenceItem: ...

    def unavailable(self, reason: str) -> EvidenceItem:
        return EvidenceItem(source=self.name, label=self.label, signal=Signal.UNAVAILABLE, summary=reason)


def date_window(loss_date: date, days_before: int, days_after: int) -> tuple[date, date]:
    return loss_date - timedelta(days=days_before), loss_date + timedelta(days=days_after)
