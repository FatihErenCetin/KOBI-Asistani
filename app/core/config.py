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
    # Birden fazla Gemini key'i virgülle yazılabilir.
    # Örn: key_1,key_2,key_3
    # Sistem 429/rate limit durumunda sıradaki key'e otomatik geçer.
    GEMINI_API_KEYS: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = "change_me"

    ADMIN_TOKEN: str = "change_me"
    ADMIN_TELEGRAM_ID: str = ""
    GROQ_API_KEY: str = ""
    SUPPLIER_EMAIL: str = ""  # Tedarikci mail adresi  # Yöneticinin Telegram kullanıcı ID'si

    STT_ENABLED: bool = False
    STT_PROVIDER: str = "gemini"

    CARGO_AUTO_ADVANCE: bool = False
    CARGO_AUTO_ADVANCE_INTERVAL_MIN: int = 2

    # Proaktif gecikme bildirimi
    PROACTIVE_NOTIFICATIONS_ENABLED: bool = False
    PROACTIVE_NOTIFICATIONS_INTERVAL_MIN: int = 30

    # Sabah brifing
    MORNING_BRIEFING_ENABLED: bool = False
    MORNING_BRIEFING_HOUR: int = 8
    MORNING_BRIEFING_MINUTE: int = 0

    # Prediktif stok tahmini
    STOCK_FORECAST_ENABLED: bool = False
    STOCK_FORECAST_INTERVAL_HOURS: int = 6

    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def gemini_api_keys_list(self) -> list[str]:
        keys: list[str] = []
        if self.GEMINI_API_KEYS.strip():
            keys.extend(k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip())
        if self.GEMINI_API_KEY.strip():
            keys.append(self.GEMINI_API_KEY.strip())
        # Aynı key iki yerde yazıldıysa tekilleştir.
        seen: set[str] = set()
        unique: list[str] = []
        for key in keys:
            if key not in seen:
                unique.append(key)
                seen.add(key)
        return unique


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
