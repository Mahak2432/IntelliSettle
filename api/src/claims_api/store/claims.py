"""Claim persistence: in memory for tests and local dev, Firestore in the cloud."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from claims_api.domain.models import Claim, ClaimStatus, ReviewThresholds

# Passed as `sandbox` to list claims from every sandbox.
ANY_SANDBOX: Any = object()


class ClaimRepository(Protocol):
    async def get(self, claim_id: str) -> Claim | None: ...
    async def save(self, claim: Claim) -> None: ...
    async def delete(self, claim_id: str) -> None: ...
    async def list(
        self,
        *,
        farmer_id: str | None = None,
        statuses: set[ClaimStatus] | None = None,
        sandbox: str | None = ANY_SANDBOX,
    ) -> list[Claim]: ...


class ThresholdStore(Protocol):
    async def get(self) -> ReviewThresholds: ...
    async def save(self, thresholds: ReviewThresholds) -> None: ...


def _matches(claim: Claim, farmer_id, statuses, sandbox) -> bool:
    return (
        (farmer_id is None or claim.farmer_id == farmer_id)
        and (statuses is None or claim.status in statuses)
        and (sandbox is ANY_SANDBOX or claim.sandbox == sandbox)
    )


def _newest_first(claims) -> list[Claim]:
    return sorted(claims, key=lambda c: c.submitted_at, reverse=True)


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    async def get(self, claim_id: str) -> Claim | None:
        claim = self._claims.get(claim_id)
        return claim.model_copy(deep=True) if claim else None

    async def save(self, claim: Claim) -> None:
        self._claims[claim.claim_id] = claim.model_copy(deep=True)

    async def delete(self, claim_id: str) -> None:
        self._claims.pop(claim_id, None)

    async def list(self, *, farmer_id=None, statuses=None, sandbox=ANY_SANDBOX) -> list[Claim]:
        return _newest_first(
            c.model_copy(deep=True)
            for c in self._claims.values()
            if _matches(c, farmer_id, statuses, sandbox)
        )


class InMemoryThresholdStore:
    def __init__(self) -> None:
        self._value = ReviewThresholds()

    async def get(self) -> ReviewThresholds:
        return self._value

    async def save(self, thresholds: ReviewThresholds) -> None:
        self._value = thresholds


class FirestoreClaimRepository:
    collection = "claims"

    def __init__(self, project: str | None) -> None:
        from google.cloud import firestore

        self._db = firestore.Client(project=project)

    async def get(self, claim_id: str) -> Claim | None:
        snap = await asyncio.to_thread(self._db.collection(self.collection).document(claim_id).get)
        return Claim.model_validate(snap.to_dict()) if snap.exists else None

    async def save(self, claim: Claim) -> None:
        ref = self._db.collection(self.collection).document(claim.claim_id)
        await asyncio.to_thread(ref.set, claim.model_dump(mode="json"))

    async def delete(self, claim_id: str) -> None:
        await asyncio.to_thread(self._db.collection(self.collection).document(claim_id).delete)

    async def list(self, *, farmer_id=None, statuses=None, sandbox=ANY_SANDBOX) -> list[Claim]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = self._db.collection(self.collection)
        if farmer_id:
            query = query.where(filter=FieldFilter("farmer_id", "==", farmer_id))
        if isinstance(sandbox, str):
            query = query.where(filter=FieldFilter("sandbox", "==", sandbox))
        docs = await asyncio.to_thread(lambda: list(query.stream()))
        claims = (Claim.model_validate(d.to_dict()) for d in docs)
        return _newest_first(c for c in claims if _matches(c, None, statuses, sandbox))


class FirestoreThresholdStore:
    def __init__(self, project: str | None) -> None:
        from google.cloud import firestore

        self._ref = firestore.Client(project=project).collection("config").document("review_thresholds")

    async def get(self) -> ReviewThresholds:
        snap = await asyncio.to_thread(self._ref.get)
        return ReviewThresholds.model_validate(snap.to_dict()) if snap.exists else ReviewThresholds()

    async def save(self, thresholds: ReviewThresholds) -> None:
        await asyncio.to_thread(self._ref.set, thresholds.model_dump())
