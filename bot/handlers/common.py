from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from bot.services.api_client import api_client, APIError

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Register or greet user on /start."""
    tg_user = message.from_user
    if tg_user is None:
        return

    try:
        user = await api_client.ensure_user(
            telegram_id=tg_user.id,
            username=tg_user.username,
            role="player",
        )
        role = user.get("role", "player")
        await message.answer(
            f"👋 Welcome, <b>{tg_user.full_name}</b>!\n"
            f"Your role: <b>{role}</b>\n"
            f"Your internal ID: <code>{user['id']}</code>\n\n"
            f"Use /help to see available commands."
        )
    except APIError as exc:
        logger.error("Failed to register user: %s", exc)
        await message.answer("⚠️ Registration failed. Please try again later.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show available commands."""
    await message.answer(
        "📖 <b>Available Commands</b>\n\n"
        "<b>Player:</b>\n"
        "/balance — Check your point balance\n"
        "/history — View your transaction history\n\n"
        "<b>Curator / Admin:</b>\n"
        "/add &lt;@username&gt; &lt;amount&gt; &lt;note&gt; — Add points\n"
        "/subtract &lt;@username&gt; &lt;amount&gt; &lt;note&gt; — Subtract points\n"
        "/penalty &lt;@username&gt; &lt;amount&gt; &lt;note&gt; — Apply penalty\n"
        "/spend &lt;@username&gt; &lt;amount&gt; &lt;note&gt; — Record spending\n\n"
        "<b>Admin:</b>\n"
        "/users — List all users\n"
        "/export — Export data as CSV\n\n"
        "<b>Other:</b>\n"
        "/setrole &lt;@username&gt; &lt;role&gt; — Set user role (admin only)\n"
        "/start — Register / re-register"
    )
