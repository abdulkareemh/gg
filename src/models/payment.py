"""Payment transaction model."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    transaction_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50))  # syriatel_cash, mtn_cash
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(5), default="SYP")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending, processing, completed, failed, refunded
    customer_phone: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
