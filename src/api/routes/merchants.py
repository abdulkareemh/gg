"""Merchant management API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db

router = APIRouter()


class MerchantCreate(BaseModel):
    phone: str
    name: str
    business_name: str
    business_type: str
    city: str
    language: str = "ar-SY"
    platform: str = "whatsapp"


class MerchantResponse(BaseModel):
    id: int
    phone: str
    name: str
    business_name: str
    business_type: str
    city: str
    plan: str
    is_active: bool


@router.post("/", response_model=dict)
async def register_merchant(merchant: MerchantCreate, db: AsyncSession = Depends(get_db)):
    """Register a new merchant on the platform."""
    # TODO: Create merchant in database
    return {
        "status": "created",
        "message": f"مرحبا {merchant.name}! تم تسجيل {merchant.business_name} بنجاح.",
        "merchant": merchant.model_dump(),
    }


@router.get("/{merchant_id}")
async def get_merchant(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get merchant details."""
    # TODO: Fetch from database
    return {"merchant_id": merchant_id, "status": "placeholder"}
