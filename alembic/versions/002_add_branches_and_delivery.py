"""Add branches and delivery zones tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Branches table
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_main", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("opening_hours", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Delivery zones table
    op.create_table(
        "delivery_zones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("delivery_fee", sa.Numeric(12, 2), default=0),
        sa.Column("min_order_amount", sa.Numeric(12, 2), default=0),
        sa.Column("estimated_minutes", sa.Integer(), default=30),
        sa.Column("is_active", sa.Boolean(), default=True),
    )


def downgrade() -> None:
    op.drop_table("delivery_zones")
    op.drop_table("branches")
