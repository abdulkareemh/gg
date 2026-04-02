"""In-process notification queue.

Replaces external message queue (Celery/RabbitMQ) dependency.
Uses asyncio for lightweight background notification delivery.

For single-server deployment, this is all you need.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    ORDER_NEW = "order_new"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_READY = "order_ready"
    ORDER_DELIVERED = "order_delivered"
    LOW_STOCK = "low_stock"
    DAILY_REPORT = "daily_report"
    PAYMENT_RECEIVED = "payment_received"
    REVIEW_RECEIVED = "review_received"
    PROMO = "promo"


@dataclass
class Notification:
    phone: str
    platform: str  # whatsapp, telegram
    type: NotificationType
    message: str
    merchant_id: int | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    attempts: int = 0
    max_attempts: int = 3


class NotificationQueue:
    """Async in-process notification queue with retry."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._dead_letter: deque[Notification] = deque(maxlen=1000)
        self._sent_count = 0
        self._failed_count = 0
        self._running = False

    async def enqueue(self, notification: Notification) -> None:
        """Add a notification to the queue."""
        await self._queue.put(notification)

    async def enqueue_simple(
        self, phone: str, message: str, platform: str = "whatsapp",
        notif_type: NotificationType = NotificationType.ORDER_NEW,
        merchant_id: int | None = None,
    ) -> None:
        """Convenience method to queue a simple notification."""
        await self.enqueue(Notification(
            phone=phone,
            platform=platform,
            type=notif_type,
            message=message,
            merchant_id=merchant_id,
        ))

    async def process(self, send_func) -> None:
        """Process notifications from the queue.

        send_func: async function(phone, text, platform) -> bool
        """
        self._running = True
        while self._running:
            try:
                notification = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            notification.attempts += 1
            try:
                success = await send_func(
                    notification.phone,
                    notification.message,
                    notification.platform,
                )
                if success:
                    self._sent_count += 1
                else:
                    raise Exception("Send returned False")
            except Exception:
                if notification.attempts < notification.max_attempts:
                    # Re-queue with backoff
                    await asyncio.sleep(2 ** notification.attempts)
                    await self._queue.put(notification)
                else:
                    self._dead_letter.append(notification)
                    self._failed_count += 1

    def stop(self):
        self._running = False

    @property
    def pending(self) -> int:
        return self._queue.qsize()

    def stats(self) -> dict:
        return {
            "pending": self.pending,
            "sent": self._sent_count,
            "failed": self._failed_count,
            "dead_letter": len(self._dead_letter),
        }


# Global queue
notification_queue = NotificationQueue()
