"""Conversation session management using Redis.

Tracks multi-turn conversations so the bot remembers context
across messages (e.g., "add another one" knows what was ordered).
"""

import json
from datetime import timedelta

import redis.asyncio as redis

from src.utils.config import settings

SESSION_TTL = timedelta(minutes=30)


class SessionService:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    def _key(self, phone: str) -> str:
        return f"noor:session:{phone}"

    async def get_session(self, phone: str) -> dict:
        """Get current conversation session for a phone number."""
        data = await self.redis.get(self._key(phone))
        if data:
            return json.loads(data)
        return {
            "phone": phone,
            "state": "idle",  # idle, onboarding, ordering, browsing
            "merchant_id": None,
            "customer_id": None,
            "cart": [],
            "history": [],  # Last N messages for context
            "step": None,  # Current step in a multi-step flow
            "temp_data": {},  # Temporary data for current flow
        }

    async def save_session(self, phone: str, session: dict) -> None:
        """Save conversation session."""
        # Keep history manageable — last 10 messages
        if len(session.get("history", [])) > 10:
            session["history"] = session["history"][-10:]

        await self.redis.set(
            self._key(phone),
            json.dumps(session, ensure_ascii=False),
            ex=int(SESSION_TTL.total_seconds()),
        )

    async def add_to_history(self, phone: str, role: str, message: str) -> dict:
        """Add a message to conversation history and return updated session."""
        session = await self.get_session(phone)
        session["history"].append({"role": role, "text": message})
        await self.save_session(phone, session)
        return session

    async def update_state(self, phone: str, state: str, step: str | None = None) -> dict:
        """Update the conversation state."""
        session = await self.get_session(phone)
        session["state"] = state
        session["step"] = step
        await self.save_session(phone, session)
        return session

    async def add_to_cart(self, phone: str, product_id: int, name_ar: str, quantity: int, price: float) -> dict:
        """Add an item to the shopping cart."""
        session = await self.get_session(phone)
        # Check if product already in cart
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
        """Clear the shopping cart."""
        session = await self.get_session(phone)
        session["cart"] = []
        await self.save_session(phone, session)
        return session

    async def clear_session(self, phone: str) -> None:
        """Delete a session entirely."""
        await self.redis.delete(self._key(phone))
