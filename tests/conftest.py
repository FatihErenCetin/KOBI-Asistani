from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base, Warehouse


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Function-scoped engine + drop/create + session + default warehouse.

    Her testte fresh schema. pytest-asyncio'nun event-loop scoping sebebiyle
    engine'i de function-scoped tutmak gerekiyor (session-scoped engine'in
    farkli bir loop'a attach olma riski var).

    M6 sonrası: stock_movements_crud.record default warehouse arıyor — fixture
    her test başında "Ana Depo" oluşturur.
    """
    engine = create_async_engine(settings.DATABASE_TEST_URL, future=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with Session() as session:
            session.add(
                Warehouse(name="Ana Depo", code="main", is_default=True, is_active=True)
            )
            await session.flush()
            yield session
    finally:
        await engine.dispose()
