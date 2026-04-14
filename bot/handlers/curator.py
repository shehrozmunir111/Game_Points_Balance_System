from __future__ import annotations

import logging
import uuid

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.api_client import api_client, APIError

logger = logging.getLogger(__name__)
router = Router()


def _parse_transaction_args(text: str) -> tuple[str, str, str] | None:
    """
    Parse: /command @username amount note text
    Returns (username, amount_str, description) or None.
    """
    parts = text.split(maxsplit=3)
    # parts[0] = /command, parts[1] = @username, parts[2] = amount, parts[3] = description
    if len(parts) < 3:
        return None
    username = parts[1].lstrip("@")
    amount_str = parts[2]
    description = parts[3] if len(parts) > 3 else ""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None
    except ValueError:
        return None
    return username, amount_str, description


async def _get_curator_or_reply(message: Message) -> dict | None:
    """Validate the calling user is a curator or admin."""
    tg_user = message.from_user
    if tg_user is None:
        return None
    try:
        user = await api_client.get_user_by_telegram(tg_user.id)
    except APIError:
        await message.answer("⚠️ You are not registered. Send /start first.")
        return None

    if user.get("role") not in ("curator", "admin"):
        await message.answer("🚫 You do not have curator/admin permissions.")
        return None
    return user


async def _handle_txn_command(message: Message, txn_type: str) -> None:
    """Generic handler for add/subtract/penalty/spend commands."""
    curator = await _get_curator_or_reply(message)
    if curator is None:
        return

    parsed = _parse_transaction_args(message.text or "")
    if parsed is None:
        await message.answer(
            f"❌ <b>Invalid format</b>\n\n"
            f"Usage: /{txn_type} @username amount note\n"
            f"Example: /{txn_type} @player1 100 game win bonus"
        )
        return

    username, amount_str, description = parsed

    # Look up the target player
    try:
        player = await api_client.get_user_by_username(username)
    except APIError:
        await message.answer(f"❌ Player <b>@{username}</b> not found. They must /start the bot first.")
        return

    # Generate unique request_id for idempotency
    request_id = f"{txn_type}-{curator['id']}-{player['id']}-{uuid.uuid4().hex[:12]}"

    try:
        result = await api_client.create_transaction(
            txn_type,
            player_id=player["id"],
            curator_id=curator["id"],
            amount=amount_str,
            description=description or None,
            request_id=request_id,
        )
        txn = result["transaction"]
        emoji = {"add": "✅", "subtract": "➖", "penalty": "🚫", "spend": "💸"}.get(txn_type, "•")
        await message.answer(
            f"{emoji} <b>Transaction Successful</b>\n\n"
            f"Type: <b>{txn_type.upper()}</b>\n"
            f"Player: <b>@{username}</b>\n"
            f"Amount: <b>{txn['amount']}</b>\n"
            f"New balance: <b>{result['new_balance']}</b>\n"
            f"Note: {description or '—'}\n"
            f"ID: <code>{txn['request_id']}</code>"
        )
        logger.info(
            "Transaction %s by curator=%s for player=%s amount=%s",
            txn_type, curator["id"], player["id"], amount_str,
        )
    except APIError as exc:
        logger.error("Transaction failed: %s", exc)
        await message.answer(f"❌ Transaction failed: {exc.detail}")


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
    await _handle_txn_command(message, "add")


@router.message(Command("subtract"))
async def cmd_subtract(message: Message) -> None:
    await _handle_txn_command(message, "subtract")


@router.message(Command("penalty"))
async def cmd_penalty(message: Message) -> None:
    await _handle_txn_command(message, "penalty")


@router.message(Command("spend"))
async def cmd_spend(message: Message) -> None:
    await _handle_txn_command(message, "spend")
