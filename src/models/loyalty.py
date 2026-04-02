"""Loyalty and rewards models."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class LoyaltyProgram(Base):
    """Merchant's loyalty program configuration."""
    __tablename__ = "loyalty_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), default="برنامج الولاء")
    points_per_syp: Mapped[float] = mapped_column(Numeric(10, 4), default=0.001)  # 1 point per 1000 SYP
    min_redeem_points: Mapped[int] = mapped_column(Integer, default=100)
    point_value_syp: Mapped[float] = mapped_column(Numeric(12, 2), default=100)  # 1 point = 100 SYP discount
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoyaltyBalance(Base):
    """Customer's loyalty points balance."""
    __tablename__ = "loyalty_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    total_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_redeemed: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoyaltyTransaction(Base):
    """Record of points earned or redeemed."""
    __tablename__ = "loyalty_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    balance_id: Mapped[int] = mapped_column(ForeignKey("loyalty_balances.id"), index=True)
    type: Mapped[str] = mapped_column(String(10))  # "earn" or "redeem"
    points: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
