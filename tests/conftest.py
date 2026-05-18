from collections.abc import AsyncGenerator

from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api_main import app
from app.core.database import get_db
from app.core.settings import settings
from app.gate.models import LeadMagnetResult, LeadMagnetRun


_engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    async with _SessionLocal() as session:
        await session.execute(delete(LeadMagnetRun))
        await session.execute(delete(LeadMagnetResult))
        await session.commit()
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _override() -> AsyncGenerator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
