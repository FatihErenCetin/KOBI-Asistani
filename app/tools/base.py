from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AgentContext:
    """Tool cagrilarinda gecirilen baglam. Her tool kendi izinlerini buradan dogrular."""

    db: AsyncSession
    customer_id: int | None = None  # Customer agent icin set edilir
    is_admin: bool = False  # Panel agent True
    telegram_user_id: int | None = None
