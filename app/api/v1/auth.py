import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.auth import (
    AuthError,
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.core.config import settings
from app.db.crud import admin_users as admin_crud
from app.db.models import AdminUser
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_admin(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Bearer JWT'yi cozumler ve aktif kullaniciyi doner.

    `/me` ve diğer JWT-only endpoint'lerin kullanacağı dependency.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except AuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sub eksik")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sub format hatasi") from e
    user = await admin_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kullanici bulunamadi veya pasif")
    return user


def _user_response(user: AdminUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Email + password ile giris. Basari -> JWT token.

    Brute-force ve timing attack koruma: hatali email'lerde de bcrypt verify cagrilir
    (kullanici varlığını sızdırmamak için).
    """
    user = await admin_crud.get_by_email(db, payload.email)
    # Timing-attack koruma: kullanici yoksa da fake hash ile verify cagir
    fake_hash = "$2b$12$" + "x" * 53  # bcrypt dummy
    target_hash = user.password_hash if user else fake_hash
    ok = verify_password(payload.password, target_hash)
    if not user or not ok or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Email veya sifre hatali",
        )
    token = create_access_token(subject=user.id, extra={"email": user.email})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_HOURS * 3600,
        user=_user_response(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Yeni admin kullanici olustur. Basarili olunca auto-login (JWT doner).

    NOT (production icin): Bu endpoint su an acik. Hackathon demo'su icin.
    Production'da:
    - Admin-only register (Depends(get_current_admin) ekle)
    - Veya invite token ile register
    """
    existing = await admin_crud.get_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Bu email zaten kayitli",
        )
    user = await admin_crud.create(
        db,
        email=payload.email,
        password=payload.password,
        name=payload.name.strip(),
    )
    await db.commit()
    token = create_access_token(subject=user.id, extra={"email": user.email})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_HOURS * 3600,
        user=_user_response(user),
    )


@router.get("/me", response_model=MeResponse)
async def me(current: AdminUser = Depends(get_current_admin)):
    """Mevcut kullaniciyi doner (token dogrulama icin de kullanilir)."""
    return _user_response(current)
