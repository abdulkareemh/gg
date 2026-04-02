"""Add loyalty, reviews, scheduled orders, and expenses tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Loyalty programs
    op.create_table(
        "loyalty_programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), unique=True, nullable=False),
        sa.Column("name", sa.String(200), default="برنامج الولاء"),
        sa.Column("points_per_syp", sa.Numeric(10, 4), default=0.001),
        sa.Column("min_redeem_points", sa.Integer(), default=100),
        sa.Column("point_value_syp", sa.Numeric(12, 2), default=100),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Loyalty balances
    op.create_table(
        "loyalty_balances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("points", sa.Integer(), default=0),
        sa.Column("total_earned", sa.Integer(), default=0),
        sa.Column("total_redeemed", sa.Integer(), default=0),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Loyalty transactions
    op.create_table(
        "loyalty_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("balance_id", sa.Integer(), sa.ForeignKey("loyalty_balances.id"), nullable=False, index=True),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="valid_rating"),
    )

    # Scheduled orders
    op.create_table(
        "scheduled_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False, index=True),
        sa.Column("items_json", sa.Text(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), default=0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="scheduled"),
        sa.Column("is_converted", sa.Boolean(), default=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Expenses
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), default="SYP"),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("scheduled_orders")
    op.drop_table("reviews")
    op.drop_table("loyalty_transactions")
    op.drop_table("loyalty_balances")
    op.drop_table("loyalty_programs")
