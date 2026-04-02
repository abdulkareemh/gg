"""Webhook retry queue for failed message deliveries.

When sending a message via WhatsApp/Telegram fails,
queue it for retry with exponential backoff.
"""

import asyncio
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque


@dataclass
class RetryItem:
    """A message that needs to be retried."""
    phone: str
    text: str
    platform: str
    attempts: int = 0
    max_attempts: int = 4
    next_retry: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def backoff_seconds(self) -> int:
        """Exponential backoff: 2s, 4s, 8s, 16s."""
        return 2 ** (self.attempts + 1)

    @property
    def should_retry(self) -> bool:
        return self.attempts < self.max_attempts

    @property
    def is_due(self) -> bool:
        return datetime.utcnow() >= self.next_retry


class RetryQueue:
    """In-memory retry queue. Use Redis in production."""

    def __init__(self):
        self._queue: deque[RetryItem] = deque()
        self._failed: list[RetryItem] = []
        self._running = False

    def enqueue(self, phone: str, text: str, platform: str):
        """Add a failed message to the retry queue."""
        item = RetryItem(phone=phone, text=text, platform=platform)
        self._queue.append(item)

    async def process(self, send_func):
        """Process the retry queue.

        Args:
            send_func: async function(phone, text, platform) -> bool
        """
        if not self._queue:
            return

        items_to_retry = []
        while self._queue:
            item = self._queue.popleft()
            if item.is_due:
                items_to_retry.append(item)
            else:
                self._queue.append(item)
                break

        for item in items_to_retry:
            try:
                success = await send_func(item.phone, item.text, item.platform)
                if success:
                    print(f"[RETRY] Message sent to {item.phone} after {item.attempts + 1} attempts")
                else:
                    raise Exception("Send returned False")
            except Exception as e:
                item.attempts += 1
                if item.should_retry:
                    item.next_retry = datetime.utcnow() + timedelta(seconds=item.backoff_seconds)
                    self._queue.append(item)
                    print(
                        f"[RETRY] Attempt {item.attempts}/{item.max_attempts} failed for {item.phone}. "
                        f"Next retry in {item.backoff_seconds}s"
                    )
                else:
                    self._failed.append(item)
                    print(f"[RETRY] Permanently failed for {item.phone} after {item.max_attempts} attempts")

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    def get_stats(self) -> dict:
        return {
            "pending": self.pending_count,
            "permanently_failed": self.failed_count,
        }


# Global retry queue
retry_queue = RetryQueue()
