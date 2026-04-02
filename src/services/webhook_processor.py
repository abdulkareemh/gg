"""Complete webhook event processor.

Unified processor that handles all incoming webhook events,
logs them to the audit trail, and routes to the right handler.
"""

import json
from datetime import datetime

from src.services.message_handler import MessageHandler
from src.services.audit_service import AuditService
from src.utils.metrics import track_message, track_order


class WebhookProcessor:
    """Processes all incoming webhook events with logging and metrics."""

    def __init__(self):
        self.message_handler = MessageHandler()

    async def process_whatsapp(self, body: dict, db_session) -> dict:
        """Process a WhatsApp webhook event."""
        audit = AuditService(db_session)
        processed = 0

        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})

                # Handle message events
                messages = value.get("messages", [])
                for msg in messages:
                    msg_type = msg.get("type", "unknown")
                    phone = msg.get("from", "unknown")

                    if msg_type == "text":
                        text = msg["text"]["body"]
                        await self._handle_text_message(phone, text, "whatsapp", audit)
                        processed += 1

                    elif msg_type == "interactive":
                        # Button or list reply
                        interactive = msg.get("interactive", {})
                        reply_type = interactive.get("type")
                        if reply_type == "button_reply":
                            text = interactive["button_reply"]["title"]
                        elif reply_type == "list_reply":
                            text = interactive["list_reply"]["title"]
                        else:
                            text = str(interactive)
                        await self._handle_text_message(phone, text, "whatsapp", audit)
                        processed += 1

                    elif msg_type in ("audio", "voice"):
                        await audit.log(
                            "voice_message", phone,
                            f"Voice message received from {phone}",
                            platform="whatsapp",
                        )
                        # TODO: Process voice via VoiceTranscriber
                        processed += 1

                    elif msg_type == "image":
                        await audit.log(
                            "image_message", phone,
                            f"Image received from {phone}",
                            platform="whatsapp",
                        )
                        processed += 1

                    elif msg_type == "document":
                        await audit.log(
                            "document_message", phone,
                            f"Document received from {phone}",
                            platform="whatsapp",
                            metadata={"mime_type": msg.get("document", {}).get("mime_type")},
                        )
                        processed += 1

                # Handle status updates
                statuses = value.get("statuses", [])
                for status in statuses:
                    await audit.log(
                        "message_status", status.get("recipient_id", "unknown"),
                        f"Message status: {status.get('status')}",
                        platform="whatsapp",
                        metadata={"status": status.get("status"), "message_id": status.get("id")},
                    )

        return {"processed": processed}

    async def process_telegram(self, update: dict, db_session) -> dict:
        """Process a Telegram webhook event."""
        audit = AuditService(db_session)

        message = update.get("message", {})
        if not message:
            return {"processed": 0}

        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        text = message.get("text", "")

        if text:
            await self._handle_text_message(chat_id, text, "telegram", audit)
            return {"processed": 1}

        # Handle other message types
        if message.get("voice"):
            await audit.log(
                "voice_message", chat_id,
                "Voice message received",
                platform="telegram",
            )

        if message.get("photo"):
            await audit.log(
                "image_message", chat_id,
                "Photo received",
                platform="telegram",
            )

        if message.get("document"):
            await audit.log(
                "document_message", chat_id,
                f"Document: {message['document'].get('file_name', 'unknown')}",
                platform="telegram",
            )

        return {"processed": 1}

    async def _handle_text_message(self, phone: str, text: str, platform: str, audit: AuditService):
        """Process a text message through the full pipeline."""
        # Track metrics
        track_message(platform)

        # Log incoming message
        await audit.log(
            "message_in", phone,
            f"Message: {text[:100]}",
            platform=platform,
            metadata={"text": text},
        )

        # Process through message handler
        try:
            response = await self.message_handler.handle_message(phone, text, platform)

            # Log outgoing response
            await audit.log(
                "message_out", "noor",
                f"Response: {response[:100]}",
                platform=platform,
                metadata={"response": response, "to": phone},
            )
        except Exception as e:
            await audit.log(
                "message_error", "system",
                f"Error processing message from {phone}: {str(e)}",
                platform=platform,
            )
