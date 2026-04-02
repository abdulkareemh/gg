"""Merchant settings and preferences."""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class MerchantSettings(Base):
    __tablename__ = "merchant_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), unique=True, index=True)

    # Notifications
    notify_new_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_low_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_daily_report: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_new_reviews: Mapped[bool] = mapped_column(Boolean, default=True)

    # Business hours
    opening_time: Mapped[str] = mapped_column(String(10), default="09:00")
    closing_time: Mapped[str] = mapped_column(String(10), default="23:00")
    closed_days: Mapped[str] = mapped_column(String(50), default="")  # comma-separated: "friday,saturday"

    # Order settings
    auto_confirm_orders: Mapped[bool] = mapped_column(Boolean, default=False)
    accept_scheduled_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    accept_reservations: Mapped[bool] = mapped_column(Boolean, default=False)
    min_order_amount: Mapped[float] = mapped_column(default=0)

    # Language & communication
    preferred_language: Mapped[str] = mapped_column(String(10), default="ar-SY")
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    away_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
