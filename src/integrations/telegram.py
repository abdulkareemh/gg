"""Telegram Bot API integration."""

import httpx

from src.utils.config import settings


class TelegramClient:
    """Client for sending messages via Telegram Bot API."""

    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def send_text(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
        """Send a text message to a Telegram chat."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/sendMessage", json=payload)
            return response.json()

    async def send_inline_keyboard(self, chat_id: str, text: str, buttons: list[list[dict]]) -> dict:
        """Send a message with inline keyboard buttons."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": buttons},
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/sendMessage", json=payload)
            return response.json()

    async def set_webhook(self, url: str) -> dict:
        """Set the webhook URL for receiving updates."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/setWebhook",
                json={"url": url},
            )
            return response.json()
