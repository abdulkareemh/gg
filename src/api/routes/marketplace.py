"""Marketplace and discovery endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.marketplace_service import MarketplaceService
from src.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/search")
async def search_merchants(
    city: str | None = None,
    business_type: str | None = None,
    q: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Search for merchants by city, type, or name."""
    svc = MarketplaceService(db)
    results = await svc.search_merchants(city=city, business_type=business_type, query=q, limit=limit)
    return {"count": len(results), "merchants": results}


@router.get("/cities")
async def list_cities(db: AsyncSession = Depends(get_db)):
    """Get cities with merchant counts."""
    svc = MarketplaceService(db)
    return {"cities": await svc.get_cities()}


@router.get("/types")
async def list_business_types(db: AsyncSession = Depends(get_db)):
    """Get business types with counts."""
    svc = MarketplaceService(db)
    return {"types": await svc.get_business_types()}


@router.get("/merchants/{merchant_id}")
async def merchant_profile(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get a full merchant profile."""
    svc = MarketplaceService(db)
    profile = await svc.get_merchant_profile(merchant_id)
    if not profile:
        return {"error": "Merchant not found"}
    return profile


@router.get("/merchants/{merchant_id}/recommendations")
async def get_recommendations(
    merchant_id: int,
    customer_id: int | None = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Get personalized product recommendations."""
    svc = RecommendationService(db)
    recs = await svc.get_recommendations(merchant_id, customer_id=customer_id, limit=limit)
    return {"recommendations": recs}
