from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password
from app.db.models import AdminUser


async def get_by_id(db: AsyncSession, user_id: int) -> AdminUser | None:
    return await db.get(AdminUser, user_id)


async def get_by_email(db: AsyncSession, email: str) -> AdminUser | None:
    res = await db.execute(
        select(AdminUser).where(AdminUser.email == email.lower().strip())
    )
    return res.scalar_one_or_none()


async def create(
    db: AsyncSession, *, email: str, password: str, name: str
) -> AdminUser:
    user = AdminUser(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        name=name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def set_password(db: AsyncSession, user: AdminUser, new_password: str) -> AdminUser:
    user.password_hash = hash_password(new_password)
    await db.flush()
    return user
