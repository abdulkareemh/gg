"""Merchant (business owner) model."""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    business_name: Mapped[str] = mapped_column(String(300))
    business_type: Mapped[str] = mapped_column(String(100))  # restaurant, shop, service
    city: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")  # free, basic, pro, enterprise
    language: Mapped[str] = mapped_column(String(10), default="ar-SY")
    platform: Mapped[str] = mapped_column(String(20), default="whatsapp")  # whatsapp, telegram
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="merchant")
    products = relationship("Product", back_populates="merchant")
    customers = relationship("Customer", back_populates="merchant")
