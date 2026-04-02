"""Data export service — CSV and JSON exports for merchants."""

import csv
import io
import json
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order import Order
from src.models.product import Product
from src.models.customer import Customer


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_orders_csv(self, merchant_id: int, days: int = 30) -> str:
        """Export orders as CSV string."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(Order).where(
                and_(Order.merchant_id == merchant_id, Order.created_at >= cutoff)
            ).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Order ID", "Customer ID", "Status", "Total (SYP)", "Payment Status", "Date"])

        for o in orders:
            writer.writerow([
                o.id, o.customer_id, o.status,
                float(o.total_amount), o.payment_status,
                o.created_at.isoformat(),
            ])

        return output.getvalue()

    async def export_products_csv(self, merchant_id: int) -> str:
        """Export product catalog as CSV."""
        result = await self.db.execute(
            select(Product).where(Product.merchant_id == merchant_id).order_by(Product.category, Product.name_ar)
        )
        products = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name (AR)", "Name (EN)", "Price (SYP)", "Category", "Stock", "Available"])

        for p in products:
            writer.writerow([
                p.id, p.name_ar, p.name, float(p.price),
                p.category or "", p.stock_quantity, p.is_available,
            ])

        return output.getvalue()

    async def export_customers_csv(self, merchant_id: int) -> str:
        """Export customers as CSV."""
        result = await self.db.execute(
            select(Customer).where(Customer.merchant_id == merchant_id).order_by(Customer.total_orders.desc())
        )
        customers = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Phone", "Name", "Total Orders", "Diaspora", "First Seen", "Last Order"])

        for c in customers:
            writer.writerow([
                c.id, c.phone, c.name or "",
                c.total_orders, c.is_diaspora,
                c.created_at.isoformat(),
                c.last_order_at.isoformat() if c.last_order_at else "",
            ])

        return output.getvalue()

    async def export_all_json(self, merchant_id: int) -> str:
        """Export all merchant data as JSON."""
        orders_csv = await self.export_orders_csv(merchant_id)
        products_csv = await self.export_products_csv(merchant_id)
        customers_csv = await self.export_customers_csv(merchant_id)

        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "merchant_id": merchant_id,
            "orders_csv": orders_csv,
            "products_csv": products_csv,
            "customers_csv": customers_csv,
        }

        return json.dumps(data, ensure_ascii=False, indent=2)
