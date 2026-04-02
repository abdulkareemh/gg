"""Database configuration — supports both PostgreSQL and SQLite.

SQLite mode: Run the entire app with ZERO external dependencies.
PostgreSQL mode: Production deployment with full performance.

Set DATABASE_URL to switch:
  SQLite:     sqlite+aiosqlite:///noor.db
  PostgreSQL: postgresql+asyncpg://user:pass@host/db
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.utils.config import settings


def _get_engine_args() -> dict:
    """Get engine arguments based on database type."""
    url = settings.database_url

    if url.startswith("sqlite"):
        return {
            "echo": settings.debug,
            "connect_args": {"check_same_thread": False},
        }
    else:
        return {
            "echo": settings.debug,
        }


engine = create_async_engine(settings.database_url, **_get_engine_args())
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    """Create all tables. Works with both SQLite and PostgreSQL."""
    async with engine.begin() as conn:
        # Import all models so they register with Base.metadata
        from src.models import merchant, customer, order, product, payment  # noqa: F401
        from src.models import branch, delivery, loyalty, review  # noqa: F401
        from src.models import scheduled_order, expense, coupon, audit  # noqa: F401
        from src.models import reservation, merchant_settings, subscription  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


def is_sqlite() -> bool:
    """Check if we're running in SQLite mode."""
    return settings.database_url.startswith("sqlite")
