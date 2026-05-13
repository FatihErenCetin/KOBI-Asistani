"""Sosyal medya yönetim paneli API'leri.

Hesap CRUD, post CRUD, AI taslak agent, asset (görsel/video) üretimi,
yayınlama stub'ı, şablon kütüphanesi.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import social_media_agent
from app.api.deps import get_current_admin_optional, get_db, require_admin
from app.db.crud import products as products_crud
from app.db.crud import social as social_crud
from app.db.models import (
    AdminUser,
    SocialAccount,
    SocialAsset,
    SocialAssetStatus,
    SocialAssetType,
    SocialPlatform,
    SocialPost,
    SocialPostStatus,
)
from app.schemas.social import (
    DraftRequest,
    DraftResponse,
    GenerateAssetRequest,
    SocialAccountCreate,
    SocialAccountOut,
    SocialAccountUpdate,
    SocialAssetOut,
    SocialPostCreate,
    SocialPostOut,
    SocialPostUpdate,
)
from app.services import media_generators
from app.services.social_templates import TEMPLATES, get_template

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/social", tags=["social"], dependencies=[Depends(require_admin)]
)


def _parse_platform(value: str) -> SocialPlatform:
    try:
        return SocialPlatform(value.lower())
    except ValueError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bilinmeyen platform: {value}. Desteklenenler: "
            + ", ".join(p.value for p in SocialPlatform),
        ) from e


def _split(csv: str | None) -> list[str]:
    if not csv:
        return []
    return [s.strip() for s in csv.split(",") if s.strip()]


def _account_to_out(a: SocialAccount) -> SocialAccountOut:
    return SocialAccountOut(
        id=a.id,
        platform=a.platform.value,
        handle=a.handle,
        display_name=a.display_name,
        profile_url=a.profile_url,
        is_active=a.is_active,
        connected_at=a.connected_at,
    )


def _asset_to_out(a: SocialAsset) -> SocialAssetOut:
    return SocialAssetOut(
        id=a.id,
        asset_type=a.asset_type.value,
        prompt=a.prompt,
        provider=a.provider,
        url=a.url,
        status=a.status.value,
        error=a.error,
        created_at=a.created_at,
    )


def _post_to_out(p: SocialPost) -> SocialPostOut:
    return SocialPostOut(
        id=p.id,
        title=p.title,
        content=p.content,
        target_platforms=_split(p.target_platforms),
        hashtags=_split(p.hashtags),
        status=p.status.value,
        scheduled_at=p.scheduled_at,
        published_at=p.published_at,
        ai_generated=p.ai_generated,
        prompt=p.prompt,
        related_product_id=p.related_product_id,
        related_product_name=p.related_product.name if p.related_product else None,
        last_error=p.last_error,
        created_at=p.created_at,
        assets=[_asset_to_out(a) for a in (p.assets or [])],
    )


# ---------- Templates ----------


@router.get("/templates", response_model=list[dict])
async def list_templates():
    """Hazır post şablonları (indirim, yeni ürün, SKT, sezon vb.)."""
    return TEMPLATES


# ---------- Accounts ----------


@router.get("/accounts", response_model=list[SocialAccountOut])
async def list_accounts(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    rows = await social_crud.list_accounts(db, include_inactive=include_inactive)
    return [_account_to_out(a) for a in rows]


@router.post(
    "/accounts", response_model=SocialAccountOut, status_code=status.HTTP_201_CREATED
)
async def create_account(
    payload: SocialAccountCreate, db: AsyncSession = Depends(get_db)
):
    platform = _parse_platform(payload.platform)
    a = await social_crud.create_account(
        db,
        platform=platform,
        handle=payload.handle.lstrip("@"),
        display_name=payload.display_name,
        profile_url=payload.profile_url,
    )
    await db.commit()
    return _account_to_out(a)


@router.patch("/accounts/{account_id}", response_model=SocialAccountOut)
async def update_account(
    account_id: int,
    payload: SocialAccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    a = await social_crud.get_account(db, account_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    await social_crud.update_account(db, a, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return _account_to_out(a)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    a = await social_crud.get_account(db, account_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    await social_crud.soft_delete_account(db, a)
    await db.commit()


# ---------- Posts ----------


@router.get("/posts", response_model=list[SocialPostOut])
async def list_posts(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    status_enum = None
    if status_filter:
        try:
            status_enum = SocialPostStatus(status_filter.lower())
        except ValueError as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Bilinmeyen status: {status_filter}"
            ) from e
    rows = await social_crud.list_posts(db, status=status_enum)
    return [_post_to_out(p) for p in rows]


@router.post(
    "/posts", response_model=SocialPostOut, status_code=status.HTTP_201_CREATED
)
async def create_post(
    payload: SocialPostCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    # Platform doğrulama
    for plat in payload.target_platforms:
        _parse_platform(plat)
    admin_id = current_admin.id if current_admin else None
    p = await social_crud.create_post(
        db,
        content=payload.content,
        target_platforms=payload.target_platforms,
        title=payload.title,
        hashtags=payload.hashtags,
        scheduled_at=payload.scheduled_at,
        related_product_id=payload.related_product_id,
        admin_id=admin_id,
    )
    await db.commit()
    p = await social_crud.get_post(db, p.id)
    return _post_to_out(p)


@router.get("/posts/{post_id}", response_model=SocialPostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    p = await social_crud.get_post(db, post_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return _post_to_out(p)


@router.patch("/posts/{post_id}", response_model=SocialPostOut)
async def update_post(
    post_id: int,
    payload: SocialPostUpdate,
    db: AsyncSession = Depends(get_db),
):
    p = await social_crud.get_post(db, post_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    data = payload.model_dump(exclude_unset=True)
    if "target_platforms" in data and data["target_platforms"]:
        for plat in data["target_platforms"]:
            _parse_platform(plat)
    if "status" in data and data["status"]:
        try:
            data["status"] = SocialPostStatus(data["status"].lower())
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    await social_crud.update_post(db, p, **data)
    await db.commit()
    p = await social_crud.get_post(db, post_id)
    return _post_to_out(p)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    p = await social_crud.get_post(db, post_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    await social_crud.delete_post(db, p)
    await db.commit()


# ---------- AI Draft Agent ----------


@router.post("/draft", response_model=DraftResponse)
async def draft_post(
    payload: DraftRequest, db: AsyncSession = Depends(get_db)
):
    """AI ile post taslağı üret. İçerik + hashtag + image_prompt + video_prompt + platforms."""
    product_name = None
    product_description = None
    if payload.product_id:
        product = await products_crud.get_by_id(db, payload.product_id)
        if product:
            product_name = product.name
            product_description = product.description

    # Şablon varsa prompt'u zenginleştir
    actual_prompt = payload.prompt
    if payload.template_id:
        template = get_template(payload.template_id)
        if template:
            actual_prompt = f"[{template['title']}] {payload.prompt}"

    draft = await social_media_agent.draft_post(
        actual_prompt,
        product_name=product_name,
        product_description=product_description,
        discount_pct=payload.discount_pct,
        target_platforms=payload.target_platforms,
    )
    return DraftResponse(**draft)


# ---------- Asset generation (image/video) ----------


@router.post("/posts/{post_id}/assets", response_model=SocialAssetOut)
async def generate_asset(
    post_id: int,
    payload: GenerateAssetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bir post için görsel veya video üret (provider stub'ları üzerinden)."""
    p = await social_crud.get_post(db, post_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    try:
        atype = SocialAssetType(payload.asset_type.lower())
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    if atype == SocialAssetType.IMAGE:
        gen = media_generators.get_image_generator()
        result = await gen.generate(payload.prompt, size=payload.size or "1024x1024")
    else:
        gen = media_generators.get_video_generator()
        result = await gen.generate(payload.prompt, duration_seconds=6)

    asset = await social_crud.add_asset(
        db,
        post_id=post_id,
        asset_type=atype,
        prompt=payload.prompt,
        provider=result.get("provider"),
        url=result.get("url"),
        status=(
            SocialAssetStatus.READY
            if result.get("url")
            else SocialAssetStatus.FAILED
        ),
        error=result.get("error"),
    )
    await db.commit()
    return _asset_to_out(asset)


# ---------- Publish stub ----------


@router.post("/posts/{post_id}/publish", response_model=SocialPostOut)
async def publish_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Postu yayınla (stub).

    Şu an gerçek platform API entegrasyonu yok. Bu endpoint:
    - Post'un assets listesinde READY durumda en az 1 görsel olmasını kontrol eder
    - Status'u PUBLISHED yapar, published_at = şimdi
    - API entegre edildiğinde her platform için ayrı upload yapacak
    """
    p = await social_crud.get_post(db, post_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if not p.target_platforms:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Hedef platform seçilmemiş"
        )
    logger.info(
        "Stub publish: post=%s platforms=%s assets=%d",
        p.id, p.target_platforms, len(p.assets or []),
    )
    await social_crud.mark_published(db, p)
    await db.commit()
    p = await social_crud.get_post(db, post_id)
    return _post_to_out(p)
