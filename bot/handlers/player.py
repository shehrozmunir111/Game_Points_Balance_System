from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.api_client import api_client, APIError

logger = logging.getLogger(__name__)
router = Router()


async def _get_user_or_reply(message: Message) -> dict | None:
    """Lookup the calling user in the backend. Reply with error if not found."""
    tg_user = message.from_user
    if tg_user is None:
        return None
    try:
        return await api_client.get_user_by_telegram(tg_user.id)
    except APIError:
        await message.answer("⚠️ You are not registered. Send /start first.")
        return None


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    user = await _get_user_or_reply(message)
    if user is None:
        return

    try:
        balance = await api_client.get_balance(user["id"])
        await message.answer(
            f"💰 <b>Your Balance</b>\n\n"
            f"Points: <b>{balance['current_balance']}</b>\n"
            f"Last updated: {balance['updated_at'][:19].replace('T', ' ')}"
        )
    except APIError as exc:
        logger.error("Balance fetch failed: %s", exc)
        await message.answer("⚠️ Could not retrieve your balance.")


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    user = await _get_user_or_reply(message)
    if user is None:
        return

    try:
        transactions = await api_client.get_history(user["id"], limit=15)
        if not transactions:
            await message.answer("📜 No transaction history yet.")
            return

        lines = ["📜 <b>Transaction History</b>\n"]
        for txn in transactions:
            emoji = {"add": "➕", "subtract": "➖", "penalty": "🚫", "spend": "💸"}.get(txn["type"], "•")
            date_str = txn["created_at"][:16].replace("T", " ")
            desc = txn.get("description") or "—"
            lines.append(
                f"{emoji} <b>{txn['type'].upper()}</b> {txn['amount']} pts\n"
                f"   {desc} ({date_str})"
            )

        await message.answer("\n".join(lines))
    except APIError as exc:
        logger.error("History fetch failed: %s", exc)
        await message.answer("⚠️ Could not retrieve your history.")
