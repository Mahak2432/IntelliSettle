"""Request authentication.

- firebase mode: verify the Firebase ID token, then look up the user's session (role + farmer).
- dev mode: trust X-Dev-Uid header so the API can be exercised locally without Firebase.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from claims_api.config import Settings, get_settings
from claims_api.container import Container, get_container
from claims_api.services.sessions import Session


@dataclass(frozen=True)
class Identity:
    uid: str
    phone: str | None = None


_firebase_ready = False


def _verify_firebase_token(token: str, project: str | None) -> dict:
    global _firebase_ready
    import firebase_admin
    from firebase_admin import auth

    if not _firebase_ready:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={"projectId": project})
        _firebase_ready = True
    return auth.verify_id_token(token)


async def identity(
    authorization: str | None = Header(default=None),
    x_dev_uid: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> Identity:
    if settings.auth_mode == "dev":
        if not x_dev_uid:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-Dev-Uid header.")
        return Identity(uid=x_dev_uid)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in first.")
    try:
        claims = await asyncio.to_thread(
            _verify_firebase_token, authorization.removeprefix("Bearer "), settings.gcp_project
        )
    except Exception:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Your session has expired. Sign in again."
        ) from None
    return Identity(uid=claims["uid"], phone=claims.get("phone_number"))


async def session(
    who: Identity = Depends(identity), container: Container = Depends(get_container)
) -> Session:
    found = await container.sessions.get(who.uid)
    if found:
        return found
    if who.phone:
        farmer = next((f for f in container.reference.farmers() if f.phone == who.phone), None)
        if farmer:
            created = Session(uid=who.uid, role="farmer", farmer_id=farmer.farmer_id)
            await container.sessions.save(created)
            return created
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Choose a demo profile first.")


async def farmer_session(s: Session = Depends(session)) -> Session:
    if s.role != "farmer" or not s.farmer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is for farmers.")
    return s


async def reviewer_session(s: Session = Depends(session)) -> Session:
    if s.role != "reviewer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is for claims officers.")
    return s
