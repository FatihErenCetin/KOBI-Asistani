from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql+asyncpg://kobi:kobi@localhost:5432/kobi_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg://kobi:kobi@localhost:5432/kobi_db"
    DATABASE_TEST_URL: str = "postgresql+asyncpg://kobi:kobi@localhost:5432/kobi_test_db"

    GEMINI_API_KEY: str = ""
    # Çoklu key fallback: virgülle ayrılmış key'ler. 429 alınınca sıradakine geçer.
    GEMINI_API_KEYS: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"
    # Admin'in Telegram chat ID'si (proaktif gecikme bildirimi için, opsiyonel)
    ADMIN_TELEGRAM_ID: str = ""

    # Prediktif stok tahmin job'u (her N saatte bir çalışır)
    STOCK_FORECAST_ENABLED: bool = False
    STOCK_FORECAST_INTERVAL_HOURS: int = 6
    STOCK_FORECAST_DAYS_AHEAD: int = 7

    # Proaktif Telegram bildirimleri (kargo gecikmesi vb.) — opt-in
    PROACTIVE_NOTIFICATIONS_ENABLED: bool = False

    # Sosyal medya görsel/video üretim provider'ları
    IMAGE_PROVIDER: str = "placeholder"  # placeholder | openai
    OPENAI_API_KEY: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = "change_me"

    ADMIN_TOKEN: str = "change_me"

    # JWT for admin panel auth (login flow)
    JWT_SECRET: str = "change_me_to_random_64_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    STT_ENABLED: bool = False
    STT_PROVIDER: str = "whisper"

    CARGO_AUTO_ADVANCE: bool = False
    CARGO_AUTO_ADVANCE_INTERVAL_MIN: int = 2

    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def gemini_api_keys_list(self) -> list[str]:
        """Tüm Gemini key'leri sırasıyla döner (GEMINI_API_KEYS + GEMINI_API_KEY)."""
        keys: list[str] = []
        if self.GEMINI_API_KEYS.strip():
            keys.extend(
                k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()
            )
        if self.GEMINI_API_KEY.strip() and self.GEMINI_API_KEY.strip() not in keys:
            keys.append(self.GEMINI_API_KEY.strip())
        return keys

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
