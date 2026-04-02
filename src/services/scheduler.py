"""Background task scheduler for Noor AI.

Handles periodic tasks:
- Daily sales reports sent to merchants
- Low-stock alerts
- Session cleanup
"""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import async_session
from src.models.merchant import Merchant
from src.models.product import Product
from src.services.order_service import OrderService
from src.services.product_service import ProductService
from src.services.notification_service import NotificationService


notification_service = NotificationService()


async def send_daily_reports():
    """Send daily sales summary to all active merchants."""
    async with async_session() as db:
        result = await db.execute(
            select(Merchant).where(Merchant.is_active == True)
        )
        merchants = result.scalars().all()

        order_svc = OrderService(db)

        for merchant in merchants:
            try:
                summary = await order_svc.get_daily_summary(merchant.id)

                if summary["order_count"] > 0:
                    await notification_service.send_daily_report(
                        phone=merchant.phone,
                        platform=merchant.platform,
                        order_count=summary["order_count"],
                        revenue=summary["total_revenue"],
                        top_product="—",  # TODO: calculate top product
                    )
            except Exception as e:
                print(f"[SCHEDULER] Failed to send daily report to merchant {merchant.id}: {e}")

    print(f"[SCHEDULER] Daily reports sent at {datetime.utcnow().isoformat()}")


async def check_low_stock_alerts():
    """Check inventory and send low-stock alerts to merchants."""
    async with async_session() as db:
        result = await db.execute(
            select(Merchant).where(Merchant.is_active == True)
        )
        merchants = result.scalars().all()

        product_svc = ProductService(db)

        for merchant in merchants:
            try:
                low_stock = await product_svc.get_low_stock(merchant.id)

                if low_stock:
                    products_data = [
                        {"name_ar": p.name_ar, "stock": p.stock_quantity}
                        for p in low_stock
                    ]
                    await notification_service.notify_merchant_low_stock(
                        phone=merchant.phone,
                        platform=merchant.platform,
                        products=products_data,
                    )
            except Exception as e:
                print(f"[SCHEDULER] Failed low-stock check for merchant {merchant.id}: {e}")

    print(f"[SCHEDULER] Low-stock alerts checked at {datetime.utcnow().isoformat()}")


async def cleanup_expired_sessions():
    """Redis sessions auto-expire via TTL, but log the cleanup."""
    print(f"[SCHEDULER] Session cleanup triggered at {datetime.utcnow().isoformat()}")


class TaskScheduler:
    """Simple async task scheduler."""

    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def _run_periodic(self, func, interval_seconds: int, name: str):
        """Run a function periodically."""
        while self._running:
            try:
                await func()
            except Exception as e:
                print(f"[SCHEDULER] Error in {name}: {e}")
            await asyncio.sleep(interval_seconds)

    async def start(self):
        """Start all scheduled tasks."""
        self._running = True
        print("[SCHEDULER] Starting background tasks...")

        self._tasks = [
            asyncio.create_task(
                self._run_periodic(send_daily_reports, 86400, "daily_reports")  # 24h
            ),
            asyncio.create_task(
                self._run_periodic(check_low_stock_alerts, 3600, "low_stock")  # 1h
            ),
            asyncio.create_task(
                self._run_periodic(cleanup_expired_sessions, 7200, "cleanup")  # 2h
            ),
        ]

    async def stop(self):
        """Stop all scheduled tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        print("[SCHEDULER] Background tasks stopped.")
