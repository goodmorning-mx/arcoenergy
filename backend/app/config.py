from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="ArcoEnergy API", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    source_commit: str = Field(default="unknown", alias="SOURCE_COMMIT")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    database_url: str = Field(
        default="postgresql+psycopg://goodmorning:goodmorning_local_password@localhost:5432/goodmorning_mvp",
        alias="DATABASE_URL",
    )
    auth_secret: str = Field(default="local-development-auth-secret-change-me-000000", alias="AUTH_JWT_SECRET")
    admin_bootstrap_email: str = Field(default="", alias="ADMIN_BOOTSTRAP_EMAIL")
    admin_bootstrap_password: str = Field(default="", alias="ADMIN_BOOTSTRAP_PASSWORD")
    organization_id: str = Field(default="arcoenergy", alias="ORGANIZATION_ID")
    google_drive_folder_id: str = Field(default="", alias="GOOGLE_DRIVE_FOLDER_ID")
    google_drive_service_account_json: str = Field(default="", alias="GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    whatsapp_phone: str = Field(default="", alias="WHATSAPP_PHONE")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
