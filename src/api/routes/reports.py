"""Reporting, reviews, loyalty, expenses, and scheduling endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.report_service import ReportService
from src.services.review_service import ReviewService
from src.services.loyalty_service import LoyaltyService
from src.services.expense_service import ExpenseService
from src.services.scheduled_order_service import ScheduledOrderService
from src.services.delivery_service import DeliveryService

router = APIRouter()


# --- Reports ---

@router.get("/{merchant_id}/reports/daily")
async def daily_report(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ReportService(db)
    return await svc.daily_report(merchant_id)


@router.get("/{merchant_id}/reports/weekly")
async def weekly_report(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ReportService(db)
    return await svc.weekly_report(merchant_id)


@router.get("/{merchant_id}/reports/monthly")
async def monthly_report(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ReportService(db)
    return await svc.monthly_report(merchant_id)


# --- Reviews ---

class ReviewCreate(BaseModel):
    customer_id: int
    rating: int
    comment: str | None = None
    order_id: int | None = None


@router.post("/{merchant_id}/reviews")
async def create_review(merchant_id: int, data: ReviewCreate, db: AsyncSession = Depends(get_db)):
    svc = ReviewService(db)
    review = await svc.create_review(
        merchant_id=merchant_id,
        customer_id=data.customer_id,
        rating=data.rating,
        comment=data.comment,
        order_id=data.order_id,
    )
    return {"review_id": review.id, "rating": review.rating}


@router.get("/{merchant_id}/reviews")
async def list_reviews(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ReviewService(db)
    reviews = await svc.get_merchant_reviews(merchant_id)
    rating = await svc.get_merchant_rating(merchant_id)
    return {
        "rating": rating,
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "reply": r.reply,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
    }


# --- Loyalty ---

class LoyaltySetup(BaseModel):
    name: str = "برنامج الولاء"
    points_per_syp: float = 0.001
    min_redeem: int = 100
    point_value: float = 100


@router.post("/{merchant_id}/loyalty/setup")
async def setup_loyalty(merchant_id: int, data: LoyaltySetup, db: AsyncSession = Depends(get_db)):
    svc = LoyaltyService(db)
    program = await svc.setup_program(
        merchant_id=merchant_id,
        name=data.name,
        points_per_syp=data.points_per_syp,
        min_redeem=data.min_redeem,
        point_value=data.point_value,
    )
    return {"program_id": program.id, "name": program.name}


@router.get("/{merchant_id}/loyalty/{customer_id}")
async def loyalty_balance(merchant_id: int, customer_id: int, db: AsyncSession = Depends(get_db)):
    svc = LoyaltyService(db)
    return await svc.get_balance_info(customer_id, merchant_id)


# --- Expenses ---

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str | None = None


@router.post("/{merchant_id}/expenses")
async def add_expense(merchant_id: int, data: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    svc = ExpenseService(db)
    expense = await svc.add_expense(
        merchant_id=merchant_id,
        amount=data.amount,
        category=data.category,
        description=data.description,
    )
    return {"expense_id": expense.id, "amount": float(expense.amount)}


@router.get("/{merchant_id}/expenses/monthly")
async def monthly_expenses(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ExpenseService(db)
    return await svc.get_monthly_expenses(merchant_id)


@router.get("/{merchant_id}/profit-loss")
async def profit_loss(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = ExpenseService(db)
    return await svc.get_profit_loss(merchant_id)


# --- Delivery Zones ---

class DeliveryZoneCreate(BaseModel):
    name: str
    city: str
    delivery_fee: float = 0
    min_order_amount: float = 0
    estimated_minutes: int = 30


@router.post("/{merchant_id}/delivery-zones")
async def add_delivery_zone(merchant_id: int, data: DeliveryZoneCreate, db: AsyncSession = Depends(get_db)):
    svc = DeliveryService(db)
    zone = await svc.create_zone(
        merchant_id=merchant_id,
        name=data.name,
        city=data.city,
        delivery_fee=data.delivery_fee,
        min_order_amount=data.min_order_amount,
        estimated_minutes=data.estimated_minutes,
    )
    return {"zone_id": zone.id, "name": zone.name}


@router.get("/{merchant_id}/delivery-zones")
async def list_delivery_zones(merchant_id: int, db: AsyncSession = Depends(get_db)):
    svc = DeliveryService(db)
    zones = await svc.get_zones(merchant_id)
    return {
        "zones": [
            {
                "id": z.id,
                "name": z.name,
                "city": z.city,
                "fee": float(z.delivery_fee),
                "min_order": float(z.min_order_amount),
                "estimated_minutes": z.estimated_minutes,
            }
            for z in zones
        ],
    }


@router.get("/{merchant_id}/delivery-check")
async def check_delivery(merchant_id: int, area: str, order_total: float = 0, db: AsyncSession = Depends(get_db)):
    svc = DeliveryService(db)
    return await svc.calculate_delivery(merchant_id, area, order_total)


# --- Scheduled Orders ---

@router.get("/{merchant_id}/scheduled-orders")
async def list_scheduled_orders(merchant_id: int, hours: int = 24, db: AsyncSession = Depends(get_db)):
    svc = ScheduledOrderService(db)
    orders = await svc.get_upcoming(merchant_id, hours_ahead=hours)
    return {
        "count": len(orders),
        "orders": [
            {
                "id": o.id,
                "scheduled_for": o.scheduled_for.isoformat(),
                "total": float(o.total_amount),
                "status": o.status,
            }
            for o in orders
        ],
    }
