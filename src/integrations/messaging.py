"""Unified messaging interface.

Abstracts WhatsApp, Telegram, and any future platform behind
a single interface. The app code never touches platform-specific
APIs directly — it uses this interface.

If no platform credentials are configured, messages are logged
to console (useful for development and demo mode).
"""

from abc import ABC, abstractmethod

import httpx

from src.utils.config import settings


class MessagingBackend(ABC):
    """Abstract messaging backend."""

    @abstractmethod
    async def send(self, to: str, text: str) -> bool:
        ...

    @abstractmethod
    async def send_interactive(self, to: str, text: str, buttons: list[dict]) -> bool:
        ...


class ConsoleBackend(MessagingBackend):
    """Prints messages to console. Used when no platform is configured."""

    async def send(self, to: str, text: str) -> bool:
        print(f"[MSG → {to}] {text}")
        return True

    async def send_interactive(self, to: str, text: str, buttons: list[dict]) -> bool:
        btn_str = " | ".join(b.get("title", "") for b in buttons)
        print(f"[MSG → {to}] {text}\n  Buttons: [{btn_str}]")
        return True


class WhatsAppBackend(MessagingBackend):
    """WhatsApp Business API backend."""

    def __init__(self):
        self.base_url = f"{settings.whatsapp_api_url}/{settings.whatsapp_phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

    async def send(self, to: str, text: str) -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self.base_url}/messages", headers=self.headers, json=payload)
                return resp.status_code == 200
        except Exception:
            return False

    async def send_interactive(self, to: str, text: str, buttons: list[dict]) -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b.get("id", str(i)), "title": b["title"]}}
                        for i, b in enumerate(buttons[:3])  # WhatsApp max 3 buttons
                    ]
                },
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self.base_url}/messages", headers=self.headers, json=payload)
                return resp.status_code == 200
        except Exception:
            return False


class TelegramBackend(MessagingBackend):
    """Telegram Bot API backend."""

    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def send(self, to: str, text: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={"chat_id": to, "text": text, "parse_mode": "HTML"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def send_interactive(self, to: str, text: str, buttons: list[dict]) -> bool:
        keyboard = [[{"text": b["title"], "callback_data": b.get("id", b["title"])}] for b in buttons]
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": to,
                        "text": text,
                        "parse_mode": "HTML",
                        "reply_markup": {"inline_keyboard": keyboard},
                    },
                )
                return resp.status_code == 200
        except Exception:
            return False


class MessagingGateway:
    """Unified messaging gateway — auto-detects available backends."""

    def __init__(self):
        self.backends: dict[str, MessagingBackend] = {}
        self._setup_backends()

    def _setup_backends(self):
        """Initialize backends based on available configuration."""
        # Always have console as fallback
        self.backends["console"] = ConsoleBackend()

        # WhatsApp — if credentials are set
        if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
            self.backends["whatsapp"] = WhatsAppBackend()

        # Telegram — if bot token is set
        if settings.telegram_bot_token:
            self.backends["telegram"] = TelegramBackend()

    def get_backend(self, platform: str) -> MessagingBackend:
        """Get the backend for a platform. Falls back to console."""
        return self.backends.get(platform, self.backends["console"])

    async def send(self, to: str, text: str, platform: str = "whatsapp") -> bool:
        """Send a message on the specified platform."""
        backend = self.get_backend(platform)
        return await backend.send(to, text)

    async def send_interactive(self, to: str, text: str, buttons: list[dict], platform: str = "whatsapp") -> bool:
        """Send a message with buttons."""
        backend = self.get_backend(platform)
        return await backend.send_interactive(to, text, buttons)

    @property
    def available_platforms(self) -> list[str]:
        """List configured platforms (excluding console)."""
        return [k for k in self.backends if k != "console"]

    @property
    def status(self) -> dict:
        return {
            "platforms": {k: type(v).__name__ for k, v in self.backends.items()},
            "whatsapp_configured": "whatsapp" in self.backends,
            "telegram_configured": "telegram" in self.backends,
        }


# Global gateway instance
messaging = MessagingGateway()
