"""Subscription and usage tracking models.

Tracks merchant subscription plans, usage limits, and billing.
No third-party payment processor — tracks usage internally,
billing can be handled manually or via mobile money.
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    # Plans: free, basic, pro, enterprise

    # Billing
    monthly_price_usd: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    billing_cycle_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Usage this cycle
    orders_this_month: Mapped[int] = mapped_column(Integer, default=0)
    messages_this_month: Mapped[int] = mapped_column(Integer, default=0)
    ai_calls_this_month: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageLog(Base):
    """Daily usage log per merchant."""
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    messages: Mapped[int] = mapped_column(Integer, default=0)
    ai_calls: Mapped[int] = mapped_column(Integer, default=0)
    revenue_syp: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
