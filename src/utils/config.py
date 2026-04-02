"""Application settings loaded from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="config/.env")

    app_name: str = "NoorAI"
    app_env: str = "development"
    debug: bool = True
    app_port: int = 8000

    # Database — defaults to SQLite (zero setup required)
    database_url: str = "sqlite+aiosqlite:///noor.db"

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

    # Payment providers
    syriatel_cash_api_key: str = ""
    mtn_cash_api_key: str = ""

    # App URL (for payment callbacks)
    app_url: str = "http://localhost:8000"



settings = Settings()
