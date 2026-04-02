"""WhatsApp Business API integration."""

import httpx

from src.utils.config import settings


class WhatsAppClient:
    """Client for sending messages via WhatsApp Business API."""

    def __init__(self):
        self.base_url = f"{settings.whatsapp_api_url}/{settings.whatsapp_phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, text: str) -> dict:
        """Send a text message to a WhatsApp number."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
            )
            return response.json()

    async def send_template(self, to: str, template_name: str, language: str = "ar") -> dict:
        """Send a template message (for initiating conversations)."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
            )
            return response.json()

    async def send_interactive_list(self, to: str, header: str, body: str, sections: list) -> dict:
        """Send an interactive list message (for menus/product lists)."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header},
                "body": {"text": body},
                "action": {
                    "button": "عرض القائمة",
                    "sections": sections,
                },
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
            )
            return response.json()
