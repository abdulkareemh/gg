"""In-memory session store — replaces Redis dependency.

Drop-in replacement for SessionService that uses in-memory LRU cache
instead of Redis. Suitable for single-server deployments.

For multi-server deployments, swap back to Redis-based SessionService.
"""

import json
from datetime import timedelta

from src.services.response_cache import LRUCache


SESSION_TTL = 1800  # 30 minutes


class MemorySessionService:
    """In-memory session manager. No Redis needed."""

    def __init__(self):
        self._store = LRUCache(max_size=50000, default_ttl=SESSION_TTL)

    def _key(self, phone: str) -> str:
        return f"session:{phone}"

    async def get_session(self, phone: str) -> dict:
        data = self._store.get(self._key(phone))
        if data:
            return data
        return {
            "phone": phone,
            "state": "idle",
            "merchant_id": None,
            "customer_id": None,
            "cart": [],
            "history": [],
            "step": None,
            "temp_data": {},
        }

    async def save_session(self, phone: str, session: dict) -> None:
        if len(session.get("history", [])) > 10:
            session["history"] = session["history"][-10:]
        self._store.set(self._key(phone), session)

    async def add_to_history(self, phone: str, role: str, message: str) -> dict:
        session = await self.get_session(phone)
        session["history"].append({"role": role, "text": message})
        await self.save_session(phone, session)
        return session

    async def update_state(self, phone: str, state: str, step: str | None = None) -> dict:
        session = await self.get_session(phone)
        session["state"] = state
        session["step"] = step
        await self.save_session(phone, session)
        return session

    async def add_to_cart(self, phone: str, product_id: int, name_ar: str, quantity: int, price: float) -> dict:
        session = await self.get_session(phone)
        for item in session["cart"]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                item["total"] = item["quantity"] * item["price"]
                await self.save_session(phone, session)
                return session

        session["cart"].append({
            "product_id": product_id,
            "name_ar": name_ar,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
        })
        await self.save_session(phone, session)
        return session

    async def clear_cart(self, phone: str) -> dict:
        session = await self.get_session(phone)
        session["cart"] = []
        await self.save_session(phone, session)
        return session

    async def clear_session(self, phone: str) -> None:
        self._store.delete(self._key(phone))

    def stats(self) -> dict:
        return self._store.stats()
