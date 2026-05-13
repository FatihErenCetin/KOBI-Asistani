"""Authentication utilities: password hashing (bcrypt) + JWT token encode/decode.

Bu modul state'siz; sadece kriptografik fonksiyonlar saglar.
Database operations CRUD katmaninda."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


class AuthError(Exception):
    """Auth/token sorunlarinda firlatilir."""


# ---------- Password hashing ----------


def hash_password(plain: str) -> str:
    """bcrypt ile sifre hashle (cost factor 12).

    Hashed value icinde salt + cost + hash hepsi bir arada,
    DB'de tek string olarak saklanir.
    """
    if not plain:
        raise AuthError("Password cannot be empty")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Plain password ile saved hash karsilastirma. Sabit zamanli karsilastirma."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------- JWT ----------


def create_access_token(*, subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """JWT olustur. `subject` user ID/email gibi.

    Token payload: {sub, exp, iat, ...extra}
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.JWT_EXPIRY_HOURS)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """JWT'yi decode et + dogrula. Exp gecmisse veya imza bozuksa AuthError firlatir."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Token suresi doldu") from e
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Gecersiz token: {e}") from e
