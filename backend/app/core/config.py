from __future__ import annotations

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:admin@localhost/game_db"
    SECRET_KEY: str = "change-me"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
