from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from bot.services.api_client import api_client, APIError

logger = logging.getLogger(__name__)
router = Router()


async def _get_admin_or_reply(message: Message) -> dict | None:
    """Validate the calling user is an admin."""
    tg_user = message.from_user
    if tg_user is None:
        return None
    try:
        user = await api_client.get_user_by_telegram(tg_user.id)
    except APIError:
        await message.answer("⚠️ You are not registered. Send /start first.")
        return None

    if user.get("role") != "admin":
        await message.answer("🚫 This command is restricted to admins.")
        return None
    return user


@router.message(Command("users"))
async def cmd_users(message: Message) -> None:
    admin = await _get_admin_or_reply(message)
    if admin is None:
        return

    try:
        users = await api_client.list_users()
        if not users:
            await message.answer("No users registered yet.")
            return

        lines = ["👥 <b>Registered Users</b>\n"]
        for u in users:
            uname = f"@{u['username']}" if u.get("username") else f"tg:{u['telegram_id']}"
            lines.append(
                f"• <b>{uname}</b> — {u['role']} (ID: {u['id']})"
            )

        await message.answer("\n".join(lines))
    except APIError as exc:
        logger.error("User list failed: %s", exc)
        await message.answer("⚠️ Could not retrieve user list.")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    admin = await _get_admin_or_reply(message)
    if admin is None:
        return

    try:
        csv_bytes = await api_client.export_data()
        if isinstance(csv_bytes, bytes):
            doc = BufferedInputFile(csv_bytes, filename="export.csv")
            await message.answer_document(doc, caption="📊 Full data export")
        else:
            await message.answer("⚠️ Unexpected response from server.")
    except APIError as exc:
        logger.error("Export failed: %s", exc)
        await message.answer("⚠️ Export failed. Please try again later.")


@router.message(Command("setrole"))
async def cmd_setrole(message: Message) -> None:
    """Admin-only: set a user's role. Usage: /setrole @username role"""
    admin = await _get_admin_or_reply(message)
    if admin is None:
        return

    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("❌ Usage: /setrole @username role\nRoles: player, curator, admin")
        return

    username = parts[1].lstrip("@")
    role = parts[2].lower()
    if role not in ("player", "curator", "admin"):
        await message.answer("❌ Invalid role. Must be: player, curator, or admin")
        return

    try:
        # Ensure user exists then re-register with new role
        target = await api_client.get_user_by_username(username)
        await api_client.ensure_user(
            telegram_id=target["telegram_id"],
            username=target.get("username"),
            role=role,
        )
        await message.answer(f"✅ Role for <b>@{username}</b> updated to <b>{role}</b>")
        logger.info("Role updated: %s -> %s by admin %s", username, role, admin["id"])
    except APIError as exc:
        logger.error("Set role failed: %s", exc)
        await message.answer(f"❌ Failed: {exc.detail}")
