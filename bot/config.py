from __future__ import annotations

from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    BOT_TOKEN: str = ""
    BACKEND_URL: str = "http://backend:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


bot_settings = BotSettings()
