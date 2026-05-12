from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Function-scoped engine + drop/create + session.

    Her testte fresh schema. pytest-asyncio'nun event-loop scoping sebebiyle
    engine'i de function-scoped tutmak gerekiyor (session-scoped engine'in
    farkli bir loop'a attach olma riski var).
    """
    engine = create_async_engine(settings.DATABASE_TEST_URL, future=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with Session() as session:
            yield session
    finally:
        await engine.dispose()
