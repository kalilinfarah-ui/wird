from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "ورد"
    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Telegram
    telegram_bot_token: str
    telegram_webhook_secret: str = ""

    # Cron task protection (shared secret with cron-job.org)
    cron_secret: str = "change_this_secret"

    # Supabase Storage
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    storage_bucket: str = "wird-files"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
