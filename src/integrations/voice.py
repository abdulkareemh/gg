"""Voice message handling for Arabic speech-to-text.

Handles voice messages received via WhatsApp/Telegram
and transcribes them to text using Claude's capabilities.
"""

import httpx
import anthropic

from src.utils.config import settings


class VoiceTranscriber:
    """Transcribes Arabic voice messages to text."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def download_whatsapp_audio(self, media_id: str) -> bytes | None:
        """Download audio file from WhatsApp media API."""
        try:
            async with httpx.AsyncClient() as client:
                # First, get the media URL
                response = await client.get(
                    f"{settings.whatsapp_api_url}/{media_id}",
                    headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                )
                data = response.json()
                media_url = data.get("url")

                if not media_url:
                    return None

                # Download the actual file
                audio_response = await client.get(
                    media_url,
                    headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                )
                return audio_response.content

        except Exception as e:
            print(f"[VOICE] Failed to download WhatsApp audio: {e}")
            return None

    async def download_telegram_audio(self, file_id: str) -> bytes | None:
        """Download audio file from Telegram API."""
        try:
            async with httpx.AsyncClient() as client:
                # Get file path
                response = await client.get(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile",
                    params={"file_id": file_id},
                )
                data = response.json()
                file_path = data.get("result", {}).get("file_path")

                if not file_path:
                    return None

                # Download the file
                audio_response = await client.get(
                    f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
                )
                return audio_response.content

        except Exception as e:
            print(f"[VOICE] Failed to download Telegram audio: {e}")
            return None

    async def transcribe_with_claude(self, description: str) -> str:
        """Use Claude to interpret a voice message description.

        Since Claude can't directly process audio, we use a workaround:
        The WhatsApp/Telegram API provides a transcription hint,
        and we use Claude to clean up and interpret the Arabic text.
        """
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=(
                    "You are a Syrian Arabic transcription assistant. "
                    "Clean up the following transcribed Arabic text. "
                    "Fix any transcription errors based on Syrian dialect context. "
                    "Return ONLY the cleaned text, nothing else."
                ),
                messages=[{"role": "user", "content": description}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"[VOICE] Claude transcription failed: {e}")
            return description

    async def handle_voice_message(
        self, platform: str, media_id: str, transcription_hint: str | None = None
    ) -> str:
        """Handle an incoming voice message.

        Returns the transcribed text.
        """
        if transcription_hint:
            # If we already have a transcription, clean it up
            return await self.transcribe_with_claude(transcription_hint)

        # If no transcription available, inform the user
        return "[رسالة صوتية] عذراً، ما بقدر أسمع الرسائل الصوتية حالياً. ممكن تكتبلي شو بدك؟"
