"""Application settings loaded from environment."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NoorAI"
    app_env: str = "development"
    debug: bool = True
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://noor:changeme@localhost:5432/noor_ai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Claude API
    anthropic_api_key: str = ""

    # WhatsApp
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""

    # Telegram
    telegram_bot_token: str = ""

    class Config:
        env_file = "config/.env"


settings = Settings()
