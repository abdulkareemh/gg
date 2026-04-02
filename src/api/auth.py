"""API key authentication middleware.

Merchants access their API endpoints via an API key
that can be generated from the dashboard.
"""

import secrets
import hashlib
from functools import wraps

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db


# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> tuple[str, str]:
    """Generate an API key and its hash.

    Returns (raw_key, hashed_key). Store the hash, give the raw key to the merchant.
    """
    raw_key = f"noor_{secrets.token_urlsafe(32)}"
    hashed = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage/comparison."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify an API key and return the associated merchant info.

    Use as a FastAPI dependency:
        @router.get("/protected")
        async def protected(merchant=Depends(verify_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # For now, use a simple lookup. In production, check hashed keys in DB.
    # This is a placeholder that allows any key starting with "noor_"
    if not api_key.startswith("noor_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # TODO: Look up hashed key in merchant_api_keys table
    # For MVP, we trust the key format
    return {"api_key": api_key, "verified": True}
