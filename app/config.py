"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Playwright Configuration
    headless: bool = True
    browser_profile_dir: str = "./storage/playwright_profile"

    # Gemini Configuration
    gemini_url: str = "https://gemini.google.com/app"
    default_model: str = "gemini-2.5-pro"
    fallback_to_flash: bool = True

    # Timeout Configuration (in milliseconds)
    page_load_timeout: int = 30000
    selector_timeout: int = 10000
    response_timeout: int = 60000

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def profile_path(self) -> Path:
        """Get the profile directory as a Path object."""
        return Path(self.browser_profile_dir).resolve()


# Global settings instance
settings = Settings()
