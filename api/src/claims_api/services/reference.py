"""Read-only reference data.

Stands in for the insurer's policy system, the state land register (Bhulekh)
and the AgriStack crop sowing registry. In production each would be its own
client behind the same methods; here they load synthetic JSON from data/seed.
"""

from __future__ import annotations

import json
from pathlib import Path

from claims_api.domain.models import Farmer, LandRecord, Policy, SowingRecord


class ReferenceData:
    def __init__(
        self,
        farmers: list[Farmer],
        policies: list[Policy],
        land_records: list[LandRecord],
        sowing_records: list[SowingRecord],
    ) -> None:
        self._farmers = {f.farmer_id: f for f in farmers}
        self._policies = {p.policy_no: p for p in policies}
        self._land = {(r.village.casefold(), r.khasra_no): r for r in land_records}
        self._sowing = {(r.farmer_id, r.khasra_no, r.season): r for r in sowing_records}

    @classmethod
    def load(cls, seed_dir: Path) -> ReferenceData:
        def read(name: str) -> list[dict]:
            path = seed_dir / f"{name}.json"
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

        return cls(
            farmers=[Farmer.model_validate(x) for x in read("farmers")],
            policies=[Policy.model_validate(x) for x in read("policies")],
            land_records=[LandRecord.model_validate(x) for x in read("land_records")],
            sowing_records=[SowingRecord.model_validate(x) for x in read("sowing_records")],
        )

    def farmer(self, farmer_id: str) -> Farmer | None:
        return self._farmers.get(farmer_id)

    def farmers(self) -> list[Farmer]:
        return list(self._farmers.values())

    def policy(self, policy_no: str) -> Policy | None:
        return self._policies.get(policy_no)

    def policies_for(self, farmer_id: str) -> list[Policy]:
        return [p for p in self._policies.values() if p.farmer_id == farmer_id]

    def land_record(self, village: str, khasra_no: str) -> LandRecord | None:
        return self._land.get((village.casefold(), khasra_no))

    def sowing_record(self, farmer_id: str, khasra_no: str, season: str) -> SowingRecord | None:
        return self._sowing.get((farmer_id, khasra_no, season))
