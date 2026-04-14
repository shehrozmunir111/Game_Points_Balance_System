from __future__ import annotations

import logging
from typing import Any

import aiohttp

from bot.config import bot_settings

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for communicating with the FastAPI backend."""

    def __init__(self) -> None:
        self.base_url = bot_settings.BACKEND_URL.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | bytes:
        url = f"{self.base_url}{path}"
        logger.info("API %s %s", method, url)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=json, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.content_type == "text/csv":
                        return await resp.read()
                    data = await resp.json()
                    if resp.status >= 400:
                        detail = data.get("detail", "Unknown error") if isinstance(data, dict) else str(data)
                        raise APIError(resp.status, detail)
                    return data
        except aiohttp.ClientError as exc:
            logger.error("API connection error: %s", exc)
            raise APIError(0, f"Cannot reach backend: {exc}")

    # ── User endpoints ────────────────────────────────────────────────────

    async def ensure_user(self, telegram_id: int, username: str | None, role: str = "player") -> dict[str, Any]:
        return await self._request("POST", "/users/ensure", json={
            "telegram_id": telegram_id,
            "username": username,
            "role": role,
        })

    async def get_user_by_telegram(self, telegram_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/users/by-telegram/{telegram_id}")

    async def get_user_by_username(self, username: str) -> dict[str, Any]:
        clean = username.lstrip("@")
        return await self._request("GET", f"/users/by-username/{clean}")

    async def list_users(self) -> list[Any]:
        return await self._request("GET", "/users")

    # ── Player endpoints ──────────────────────────────────────────────────

    async def get_balance(self, player_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/players/{player_id}/balance")

    async def get_history(self, player_id: int, limit: int = 20) -> list[Any]:
        return await self._request("GET", f"/players/{player_id}/history", params={"limit": limit})

    # ── Transaction endpoints ─────────────────────────────────────────────

    async def create_transaction(
        self,
        txn_type: str,
        *,
        player_id: int,
        curator_id: int,
        amount: str,
        description: str | None,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._request("POST", f"/transactions/{txn_type}", json={
            "player_id": player_id,
            "curator_id": curator_id,
            "amount": amount,
            "description": description,
            "request_id": request_id,
        })

    # ── Export ─────────────────────────────────────────────────────────────

    async def export_data(self) -> bytes:
        return await self._request("GET", "/export")


class APIError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"API Error {status}: {detail}")


api_client = APIClient()
