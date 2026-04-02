"""Reservation / waitlist model for restaurants."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    customer_phone: Mapped[str] = mapped_column(String(20), index=True)
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    party_size: Mapped[int] = mapped_column(Integer, default=2)
    reserved_for: Mapped[datetime] = mapped_column(DateTime, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending, confirmed, seated, completed, cancelled, no_show
    is_waitlist: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
