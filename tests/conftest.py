"""Shared test fixtures — uses SQLite for fast integration tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.database import Base

# Import all models so they register with Base.metadata
from src.models.merchant import Merchant  # noqa: F401
from src.models.customer import Customer  # noqa: F401
from src.models.order import Order, OrderItem  # noqa: F401
from src.models.product import Product  # noqa: F401
from src.models.payment import Payment  # noqa: F401
from src.models.branch import Branch  # noqa: F401
from src.models.delivery import DeliveryZone  # noqa: F401


TEST_DB_URL = "sqlite+aiosqlite:///test.db"


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh test database for each test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
