from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError, decode_access_token
from app.core.config import settings
from app.db.crud import admin_users as admin_crud
from app.db.models import AdminUser
from app.db.session import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_current_admin_optional(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AdminUser | None:
    """Audit icin admin kimligi tasiyici.

    - JWT geçerli ise AdminUser nesnesi doner (audit imzasi alabilirsiniz).
    - ADMIN_TOKEN legacy yolu ise None doner (kimlik bilinmiyor; audit'te null kalir).
    - Geçersiz token ise None (require_admin zaten 401 ile kapida ret eder).

    Bu dependency 401 ATMAZ — sadece kimlik tasiyici. Endpoint'te `require_admin`
    ile birlikte kullanin: require_admin kapi bekcisi, bu kimlik gozlukleri.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if settings.ADMIN_TOKEN and token == settings.ADMIN_TOKEN:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))
    except (AuthError, ValueError, TypeError):
        return None
    if user_id <= 0:
        return None
    user = await admin_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return user


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
