"""Application settings, loaded from environment variables."""
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


settings = Settings()
