"""Simulated disbursement. Stands in for NCIP / DigiClaim pushing money over DBT rails."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from claims_api.domain.models import Farmer, PayoutRecord


class SimulatedPayoutRail:
    rail = "DBT via IMPS (simulated)"

    async def pay(self, amount_inr: int, farmer: Farmer, at: datetime | None = None) -> PayoutRecord:
        at = at or datetime.now(UTC)
        return PayoutRecord(
            amount_inr=amount_inr,
            reference=f"SIM{at:%y%m%d}{secrets.token_hex(4).upper()}",
            rail=self.rail,
            account_masked=farmer.bank.account_masked,
            paid_at=at,
        )
