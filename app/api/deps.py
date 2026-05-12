from collections.abc import AsyncIterator

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def require_admin(authorization: str | None = Header(default=None)) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid token")
    return True
