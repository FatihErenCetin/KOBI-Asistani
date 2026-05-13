from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    SocialAccount,
    SocialAsset,
    SocialAssetStatus,
    SocialAssetType,
    SocialPlatform,
    SocialPost,
    SocialPostStatus,
)


# ---------- Accounts ----------


async def list_accounts(
    db: AsyncSession, include_inactive: bool = False
) -> list[SocialAccount]:
    stmt = select(SocialAccount)
    if not include_inactive:
        stmt = stmt.where(SocialAccount.is_active.is_(True))
    stmt = stmt.order_by(SocialAccount.platform, SocialAccount.handle)
    res = await db.execute(stmt)
    return list(res.scalars())


async def get_account(db: AsyncSession, account_id: int) -> SocialAccount | None:
    return await db.get(SocialAccount, account_id)


async def create_account(
    db: AsyncSession,
    *,
    platform: SocialPlatform,
    handle: str,
    display_name: str | None = None,
    profile_url: str | None = None,
) -> SocialAccount:
    a = SocialAccount(
        platform=platform,
        handle=handle,
        display_name=display_name,
        profile_url=profile_url,
        is_active=True,
    )
    db.add(a)
    await db.flush()
    return a


async def update_account(
    db: AsyncSession, account: SocialAccount, **fields
) -> SocialAccount:
    for k, v in fields.items():
        if v is not None and hasattr(account, k):
            setattr(account, k, v)
    await db.flush()
    return account


async def soft_delete_account(
    db: AsyncSession, account: SocialAccount
) -> SocialAccount:
    account.is_active = False
    await db.flush()
    return account


# ---------- Posts ----------


async def list_posts(
    db: AsyncSession,
    status: SocialPostStatus | None = None,
    limit: int = 100,
) -> list[SocialPost]:
    stmt = select(SocialPost).options(
        selectinload(SocialPost.assets),
        selectinload(SocialPost.related_product),
    )
    if status is not None:
        stmt = stmt.where(SocialPost.status == status)
    stmt = stmt.order_by(desc(SocialPost.created_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars())


async def get_post(db: AsyncSession, post_id: int) -> SocialPost | None:
    res = await db.execute(
        select(SocialPost)
        .where(SocialPost.id == post_id)
        .options(
            selectinload(SocialPost.assets),
            selectinload(SocialPost.related_product),
        )
    )
    return res.scalar_one_or_none()


async def create_post(
    db: AsyncSession,
    *,
    content: str,
    target_platforms: list[str],
    title: str | None = None,
    hashtags: list[str] | None = None,
    scheduled_at: datetime | None = None,
    ai_generated: bool = False,
    prompt: str | None = None,
    related_product_id: int | None = None,
    admin_id: int | None = None,
) -> SocialPost:
    p = SocialPost(
        title=title,
        content=content,
        target_platforms=",".join(target_platforms),
        hashtags=",".join(hashtags) if hashtags else None,
        status=SocialPostStatus.SCHEDULED if scheduled_at else SocialPostStatus.DRAFT,
        scheduled_at=scheduled_at,
        ai_generated=ai_generated,
        prompt=prompt,
        related_product_id=related_product_id,
        created_by_admin_id=admin_id,
    )
    db.add(p)
    await db.flush()
    return p


async def update_post(db: AsyncSession, post: SocialPost, **fields) -> SocialPost:
    for k, v in fields.items():
        if v is None:
            continue
        if k == "target_platforms" and isinstance(v, list):
            post.target_platforms = ",".join(v)
        elif k == "hashtags" and isinstance(v, list):
            post.hashtags = ",".join(v) if v else None
        elif hasattr(post, k):
            setattr(post, k, v)
    await db.flush()
    return post


async def delete_post(db: AsyncSession, post: SocialPost) -> None:
    await db.delete(post)
    await db.flush()


async def mark_published(db: AsyncSession, post: SocialPost) -> SocialPost:
    post.status = SocialPostStatus.PUBLISHED
    post.published_at = datetime.utcnow()
    await db.flush()
    return post


async def mark_failed(
    db: AsyncSession, post: SocialPost, error: str
) -> SocialPost:
    post.status = SocialPostStatus.FAILED
    post.last_error = error[:500]
    await db.flush()
    return post


# ---------- Assets ----------


async def add_asset(
    db: AsyncSession,
    *,
    post_id: int,
    asset_type: SocialAssetType,
    prompt: str | None = None,
    provider: str | None = None,
    url: str | None = None,
    status: SocialAssetStatus = SocialAssetStatus.PENDING,
    error: str | None = None,
) -> SocialAsset:
    a = SocialAsset(
        post_id=post_id,
        asset_type=asset_type,
        prompt=prompt,
        provider=provider,
        url=url,
        status=status,
        error=error,
    )
    db.add(a)
    await db.flush()
    return a
