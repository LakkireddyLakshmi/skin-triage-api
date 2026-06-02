"""Application settings, loaded from environment variables."""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "Skin Triage API"
    environment: str = "development"

    # Database (used from Step 3 onward). Defaults to a local SQLite file
    # so the app runs with zero setup; in production this is a Postgres URL.
    database_url: str = "sqlite+aiosqlite:///./skin_triage.db"

    # Auth (used from Step 2 onward).
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    # The already-deployed model that does the actual prediction (Step 4).
    hf_space_url: str = "https://huggingface.co/spaces/sweety783/skin-disease-classifier"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _use_async_driver(cls, value: str) -> str:
        """Hosts (Render/Railway) hand out 'postgres://' URLs; our async engine
        needs the asyncpg driver. Rewrite the scheme so deploys 'just work'."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


settings = Settings()
