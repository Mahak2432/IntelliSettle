"""Which role and farmer a signed-in Firebase user is acting as.

For the demo, anyone can pick a farmer persona or the reviewer role. With real
phone sign-in, the farmer is matched by phone number instead.
"""

from __future__ import annotations

import asyncio
from typing import Literal, Protocol

from pydantic import BaseModel

Role = Literal["farmer", "reviewer"]


class Session(BaseModel):
    uid: str
    role: Role
    farmer_id: str | None = None


class SessionStore(Protocol):
    async def get(self, uid: str) -> Session | None: ...
    async def save(self, session: Session) -> None: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    async def get(self, uid: str) -> Session | None:
        return self._sessions.get(uid)

    async def save(self, session: Session) -> None:
        self._sessions[session.uid] = session


class FirestoreSessionStore:
    def __init__(self, project: str | None) -> None:
        from google.cloud import firestore

        self._col = firestore.Client(project=project).collection("sessions")

    async def get(self, uid: str) -> Session | None:
        snap = await asyncio.to_thread(self._col.document(uid).get)
        return Session.model_validate(snap.to_dict()) if snap.exists else None

    async def save(self, session: Session) -> None:
        await asyncio.to_thread(self._col.document(session.uid).set, session.model_dump())
