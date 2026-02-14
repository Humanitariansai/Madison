from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # AI / LLM
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini/gemini-2.0-flash"

    # Concurrency
    AUDIT_CONCURRENCY: int = Field(default=1, ge=1)

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if not self.GEMINI_API_KEY and not self.OPENAI_API_KEY:
            raise ValueError("Either GEMINI_API_KEY or OPENAI_API_KEY must be set.")
        return self


# TODO: For better testability, replace this module-level singleton with:
#   from functools import lru_cache
#   @lru_cache
#   def get_settings() -> Settings:
#       return Settings()
# Then inject via FastAPI's Depends(get_settings) in route handlers.
# This allows overriding settings in tests with app.dependency_overrides.
# See: https://fastapi.tiangolo.com/advanced/settings/
settings = Settings()
