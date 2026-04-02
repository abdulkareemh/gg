"""Webhook endpoints for WhatsApp and Telegram."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.services.message_handler import MessageHandler
from src.utils.config import settings

router = APIRouter()
handler = MessageHandler()


class TelegramUpdate(BaseModel):
    """Simplified Telegram update model."""
    update_id: int
    message: dict | None = None


# --- WhatsApp Webhook ---

@router.get("/whatsapp")
async def whatsapp_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """WhatsApp webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def whatsapp_incoming(request: Request):
    """Handle incoming WhatsApp messages."""
    body = await request.json()

    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                if msg.get("type") == "text":
                    phone = msg["from"]
                    text = msg["text"]["body"]
                    await handler.handle_message(
                        phone=phone,
                        text=text,
                        platform="whatsapp",
                    )

    return {"status": "ok"}


# --- Telegram Webhook ---

@router.post("/telegram")
async def telegram_incoming(update: TelegramUpdate):
    """Handle incoming Telegram messages."""
    if not update.message:
        return {"status": "ok"}

    chat = update.message.get("chat", {})
    text = update.message.get("text", "")
    phone = str(chat.get("id", ""))

    if text:
        await handler.handle_message(
            phone=phone,
            text=text,
            platform="telegram",
        )

    return {"status": "ok"}
