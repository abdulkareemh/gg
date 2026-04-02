"""Merchant management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.merchant_service import MerchantService
from src.services.product_service import ProductService
from src.services.order_service import OrderService

router = APIRouter()


class MerchantCreate(BaseModel):
    phone: str
    name: str
    business_name: str
    business_type: str
    city: str
    language: str = "ar-SY"
    platform: str = "whatsapp"


class ProductCreate(BaseModel):
    name: str
    name_ar: str
    price: float
    category: str | None = None
    stock_quantity: int = 0
    description: str | None = None


class ProductBulkCreate(BaseModel):
    products: list[ProductCreate]


# --- Merchant Endpoints ---

@router.post("/")
async def register_merchant(data: MerchantCreate, db: AsyncSession = Depends(get_db)):
    """Register a new merchant on the platform."""
    svc = MerchantService(db)

    existing = await svc.get_by_phone(data.phone)
    if existing:
        raise HTTPException(status_code=409, detail="Phone number already registered")

    merchant = await svc.create(
        phone=data.phone,
        name=data.name,
        business_name=data.business_name,
        business_type=data.business_type,
        city=data.city,
        platform=data.platform,
        language=data.language,
    )
    return {
        "status": "created",
        "message": f"مرحبا {merchant.name}! تم تسجيل {merchant.business_name} بنجاح.",
        "merchant_id": merchant.id,
    }


@router.get("/{merchant_id}")
async def get_merchant(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get merchant details."""
    svc = MerchantService(db)
    merchant = await svc.get_by_id(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return {
        "id": merchant.id,
        "phone": merchant.phone,
        "name": merchant.name,
        "business_name": merchant.business_name,
        "business_type": merchant.business_type,
        "city": merchant.city,
        "plan": merchant.plan,
        "is_active": merchant.is_active,
    }


# --- Product Endpoints ---

@router.post("/{merchant_id}/products")
async def add_product(merchant_id: int, data: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Add a product to merchant's catalog."""
    svc = ProductService(db)
    product = await svc.create(
        merchant_id=merchant_id,
        name=data.name,
        name_ar=data.name_ar,
        price=data.price,
        category=data.category,
        stock_quantity=data.stock_quantity,
        description=data.description,
    )
    return {"status": "created", "product_id": product.id, "name_ar": product.name_ar}


@router.post("/{merchant_id}/products/bulk")
async def add_products_bulk(merchant_id: int, data: ProductBulkCreate, db: AsyncSession = Depends(get_db)):
    """Bulk add products to merchant's catalog."""
    svc = ProductService(db)
    products = await svc.bulk_create_from_list(
        merchant_id=merchant_id,
        products_data=[p.model_dump() for p in data.products],
    )
    return {"status": "created", "count": len(products)}


@router.get("/{merchant_id}/products")
async def list_products(merchant_id: int, category: str | None = None, db: AsyncSession = Depends(get_db)):
    """List merchant's product catalog."""
    svc = ProductService(db)
    products = await svc.get_catalog(merchant_id, category=category)
    return {
        "count": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "name_ar": p.name_ar,
                "price": float(p.price),
                "category": p.category,
                "stock": p.stock_quantity,
                "available": p.is_available,
            }
            for p in products
        ],
    }


@router.get("/{merchant_id}/products/low-stock")
async def low_stock_alert(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get products with low stock."""
    svc = ProductService(db)
    products = await svc.get_low_stock(merchant_id)
    return {
        "count": len(products),
        "products": [
            {"id": p.id, "name_ar": p.name_ar, "stock": p.stock_quantity, "threshold": p.low_stock_threshold}
            for p in products
        ],
    }


# --- Order Endpoints ---

@router.get("/{merchant_id}/orders")
async def list_orders(merchant_id: int, status: str | None = None, db: AsyncSession = Depends(get_db)):
    """List merchant's orders."""
    svc = OrderService(db)
    orders = await svc.get_merchant_orders(merchant_id, status=status)
    return {
        "count": len(orders),
        "orders": [
            {
                "id": o.id,
                "customer_id": o.customer_id,
                "status": o.status,
                "total": float(o.total_amount),
                "payment_status": o.payment_status,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }


@router.get("/{merchant_id}/orders/summary")
async def daily_summary(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get today's order summary."""
    svc = OrderService(db)
    summary = await svc.get_daily_summary(merchant_id)
    return summary


@router.patch("/{merchant_id}/orders/{order_id}/status")
async def update_order_status(
    merchant_id: int, order_id: int, status: str, db: AsyncSession = Depends(get_db)
):
    """Update order status."""
    svc = OrderService(db)
    order = await svc.update_status(order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or invalid status")
    return {"order_id": order.id, "status": order.status}
