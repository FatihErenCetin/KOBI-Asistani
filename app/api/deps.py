from collections.abc import AsyncIterator

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError, decode_access_token
from app.core.config import settings
from app.db.session import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def require_admin(authorization: str | None = Header(default=None)) -> bool:
    """Admin auth dependency.

    Iki yontemi kabul eder (hibrit, geriye donuk uyum):
    1. JWT (access_token via /auth/login) — yeni standart
    2. ADMIN_TOKEN (env'deki ortak sirret) — eski, hala destekleniyor

    Returns: True (downstream'in baska bir seye ihtiyaci yok — sadece kapi).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()

    # 1. ADMIN_TOKEN match (legacy)
    if settings.ADMIN_TOKEN and token == settings.ADMIN_TOKEN:
        return True

    # 2. JWT decode dene
    try:
        payload = decode_access_token(token)
        if payload.get("sub"):
            return True
    except AuthError:
        pass

    raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid token")
