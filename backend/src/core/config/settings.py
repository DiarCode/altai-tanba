from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------- Basic App ----------
    APP_NAME: str = "AltaiTanba"
    APP_ENV: str = "development"
    FASTAPI_API_V1_PATH: str = "/api/v1"

    # ---------- Database ----------
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: int
    DB_HOST: str

    PG_EMAIL: str
    PG_PASSWORD: str

    DATABASE_URL: str  # полный URL, как у тебя в .env

    # ---------- Security / Server ----------
    SECURITY_BACKEND_CORS_ORIGINS: str
    SECURITY_ALLOWED_HOSTS: str
    SERVER_PORT: int
    USE_STUB_ADAPTER: bool

    # ---------- S3 / MinIO ----------
    S3_ACCESS_ENDPOINT: str
    S3_RESPONSE_ENDPOINT: str
    S3_REGION: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str
    S3_IMAGE_PREFIX: str
    S3_AUDIO_PREFIX: str
    S3_PATH_STYLE: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Глобальные настройки.
    
    """
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        missing_fields: list[str] = []

        for err in e.errors():
            # Для отсутствующих env-значений тип обычно "missing"
            if err.get("type") == "missing":
                loc = err.get("loc") or []
                if loc:
                    missing_fields.append(str(loc[-1]))

        if not missing_fields:
            raise

        fields_str = ", ".join(missing_fields)
        msg = f"Missing required environment variables: {fields_str}"
        raise RuntimeError(msg)


settings = get_settings()
