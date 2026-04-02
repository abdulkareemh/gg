"""Delivery zone model."""

from sqlalchemy import String, Integer, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))  # e.g., "المزة", "باب توما"
    city: Mapped[str] = mapped_column(String(100))
    delivery_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    min_order_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
