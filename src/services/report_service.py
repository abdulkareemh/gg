"""Report generation service.

Generates formatted business reports that can be sent
via chat or exported as structured data.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.customer import Customer
from src.models.payment import Payment


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def daily_report(self, merchant_id: int, date: datetime | None = None) -> dict:
        """Generate a comprehensive daily business report."""
        if date is None:
            date = datetime.utcnow()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Orders
        orders_result = await self.db.execute(
            select(
                func.count(Order.id).label("count"),
                func.sum(Order.total_amount).label("revenue"),
            ).where(and_(
                Order.merchant_id == merchant_id,
                Order.created_at >= day_start,
                Order.created_at < day_end,
            ))
        )
        orders_row = orders_result.one()

        # Order status breakdown
        status_result = await self.db.execute(
            select(Order.status, func.count(Order.id)).where(and_(
                Order.merchant_id == merchant_id,
                Order.created_at >= day_start,
                Order.created_at < day_end,
            )).group_by(Order.status)
        )
        status_breakdown = {r[0]: r[1] for r in status_result.all()}

        # Top products today
        top_products = await self.db.execute(
            select(
                Product.name_ar,
                func.sum(OrderItem.quantity).label("qty"),
                func.sum(OrderItem.total_price).label("revenue"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(and_(
                Order.merchant_id == merchant_id,
                Order.created_at >= day_start,
                Order.created_at < day_end,
            ))
            .group_by(Product.id, Product.name_ar)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )

        # New customers today
        new_customers = await self.db.execute(
            select(func.count(Customer.id)).where(and_(
                Customer.merchant_id == merchant_id,
                Customer.created_at >= day_start,
                Customer.created_at < day_end,
            ))
        )

        return {
            "date": day_start.strftime("%Y-%m-%d"),
            "orders": {
                "total": orders_row.count or 0,
                "revenue": float(orders_row.revenue or 0),
                "status_breakdown": status_breakdown,
            },
            "top_products": [
                {"name_ar": r.name_ar, "quantity": int(r.qty), "revenue": float(r.revenue)}
                for r in top_products.all()
            ],
            "new_customers": new_customers.scalar() or 0,
            "currency": "SYP",
        }

    async def weekly_report(self, merchant_id: int) -> dict:
        """Generate a weekly business report."""
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)

        # Daily breakdown
        daily_data = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_report = await self.daily_report(merchant_id, day)
            daily_data.append({
                "date": day_report["date"],
                "orders": day_report["orders"]["total"],
                "revenue": day_report["orders"]["revenue"],
            })

        total_orders = sum(d["orders"] for d in daily_data)
        total_revenue = sum(d["revenue"] for d in daily_data)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # Best day
        best_day = max(daily_data, key=lambda d: d["revenue"]) if daily_data else None

        return {
            "period": f"{week_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": round(avg_order_value),
            "daily_breakdown": daily_data,
            "best_day": best_day,
            "currency": "SYP",
        }

    async def monthly_report(self, merchant_id: int) -> dict:
        """Generate a monthly business report."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Overall stats
        result = await self.db.execute(
            select(
                func.count(Order.id),
                func.sum(Order.total_amount),
            ).where(and_(
                Order.merchant_id == merchant_id,
                Order.created_at >= month_start,
            ))
        )
        row = result.one()

        # Payment stats
        payment_result = await self.db.execute(
            select(
                Payment.provider,
                func.count(Payment.id),
                func.sum(Payment.amount),
            ).where(and_(
                Payment.merchant_id == merchant_id,
                Payment.status == "completed",
                Payment.created_at >= month_start,
            )).group_by(Payment.provider)
        )

        # Customer growth
        customer_result = await self.db.execute(
            select(func.count(Customer.id)).where(and_(
                Customer.merchant_id == merchant_id,
                Customer.created_at >= month_start,
            ))
        )

        return {
            "month": month_start.strftime("%Y-%m"),
            "total_orders": row[0] or 0,
            "total_revenue": float(row[1] or 0),
            "new_customers": customer_result.scalar() or 0,
            "payments": [
                {"provider": r[0], "count": r[1], "total": float(r[2] or 0)}
                for r in payment_result.all()
            ],
            "currency": "SYP",
        }


def format_daily_report(report: dict) -> str:
    """Format daily report as Arabic chat message."""
    orders = report["orders"]
    top = report.get("top_products", [])

    lines = [
        f"📊 تقرير يوم {report['date']}",
        f"",
        f"📦 الطلبيات: {orders['total']}",
        f"💰 الإيرادات: {orders['revenue']:,.0f} ل.س",
        f"👤 زبائن جدد: {report['new_customers']}",
    ]

    if orders.get("status_breakdown"):
        completed = orders["status_breakdown"].get("completed", 0)
        cancelled = orders["status_breakdown"].get("cancelled", 0)
        if completed:
            lines.append(f"✅ مكتملة: {completed}")
        if cancelled:
            lines.append(f"❌ ملغية: {cancelled}")

    if top:
        lines.append(f"\n🏆 الأكثر طلباً:")
        for i, p in enumerate(top[:3], 1):
            lines.append(f"  {i}. {p['name_ar']} ({p['quantity']} حبة)")

    return "\n".join(lines)


def format_weekly_report(report: dict) -> str:
    """Format weekly report as Arabic chat message."""
    lines = [
        f"📊 التقرير الأسبوعي",
        f"📅 {report['period']}",
        f"",
        f"📦 إجمالي الطلبيات: {report['total_orders']}",
        f"💰 إجمالي الإيرادات: {report['total_revenue']:,.0f} ل.س",
        f"📈 متوسط قيمة الطلب: {report['avg_order_value']:,.0f} ل.س",
    ]

    if report.get("best_day"):
        bd = report["best_day"]
        lines.append(f"\n🌟 أفضل يوم: {bd['date']} ({bd['revenue']:,.0f} ل.س)")

    if report.get("daily_breakdown"):
        lines.append(f"\n📅 التفصيل اليومي:")
        for d in report["daily_breakdown"]:
            bar = "█" * min(int(d["orders"] / 2), 20) if d["orders"] > 0 else "░"
            lines.append(f"  {d['date'][-5:]}: {bar} {d['orders']}")

    return "\n".join(lines)
