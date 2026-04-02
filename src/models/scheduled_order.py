"""Scheduled/pre-order model."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ScheduledOrder(Base):
    """An order scheduled for future fulfillment."""
    __tablename__ = "scheduled_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, index=True)
    items_json: Mapped[str] = mapped_column(Text)  # JSON-encoded items
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # scheduled -> reminded -> converted -> cancelled
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
