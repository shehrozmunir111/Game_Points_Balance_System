from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.balance import Balance
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserService:
    """Handles user creation, lookup, and listing."""

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        clean = username.lstrip("@")
        result = await session.execute(select(User).where(User.username == clean))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[User]:
        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        role: UserRole = UserRole.player,
    ) -> User:
        user = User(telegram_id=telegram_id, username=username, role=role)
        session.add(user)
        await session.flush()

        balance = Balance(player_id=user.id, current_balance=Decimal("0.00"))
        session.add(balance)
        await session.flush()

        logger.info("Created user id=%s tg=%s role=%s", user.id, telegram_id, role.value)
        return user

    @staticmethod
    async def ensure_user(
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        role: UserRole = UserRole.player,
    ) -> User:
        """Get existing user or create a new one within the current transaction."""
        user = await UserService.get_by_telegram_id(session, telegram_id)
        if user is not None:
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if user.role != role:
                logger.info("Updating role for user id=%s from %s to %s", user.id, user.role.value, role.value)
                user.role = role
                changed = True
            if changed:
                await session.flush()
            return user
        return await UserService.create_user(session, telegram_id, username, role)
