"""Add composite indexes and subscription tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), unique=True, nullable=False),
        sa.Column("plan", sa.String(20), default="free"),
        sa.Column("monthly_price_usd", sa.Numeric(8, 2), default=0),
        sa.Column("billing_cycle_start", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_trial", sa.Boolean(), default=False),
        sa.Column("trial_ends_at", sa.DateTime(), nullable=True),
        sa.Column("orders_this_month", sa.Integer(), default=0),
        sa.Column("messages_this_month", sa.Integer(), default=0),
        sa.Column("ai_calls_this_month", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Usage logs
    op.create_table(
        "usage_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("date", sa.DateTime(), nullable=False, index=True),
        sa.Column("orders", sa.Integer(), default=0),
        sa.Column("messages", sa.Integer(), default=0),
        sa.Column("ai_calls", sa.Integer(), default=0),
        sa.Column("revenue_syp", sa.Numeric(14, 2), default=0),
    )

    # Composite indexes for common queries
    op.create_index("ix_orders_merchant_status", "orders", ["merchant_id", "status"])
    op.create_index("ix_orders_merchant_date", "orders", ["merchant_id", "created_at"])
    op.create_index("ix_orders_customer_date", "orders", ["customer_id", "created_at"])
    op.create_index("ix_customers_merchant_phone", "customers", ["merchant_id", "phone"])
    op.create_index("ix_products_merchant_category", "products", ["merchant_id", "category"])
    op.create_index("ix_products_merchant_available", "products", ["merchant_id", "is_available"])
    op.create_index("ix_audit_merchant_type_date", "audit_logs", ["merchant_id", "event_type", "created_at"])
    op.create_index("ix_reviews_merchant_rating", "reviews", ["merchant_id", "rating"])


def downgrade() -> None:
    op.drop_index("ix_reviews_merchant_rating")
    op.drop_index("ix_audit_merchant_type_date")
    op.drop_index("ix_products_merchant_available")
    op.drop_index("ix_products_merchant_category")
    op.drop_index("ix_customers_merchant_phone")
    op.drop_index("ix_orders_customer_date")
    op.drop_index("ix_orders_merchant_date")
    op.drop_index("ix_orders_merchant_status")
    op.drop_table("usage_logs")
    op.drop_table("subscriptions")
