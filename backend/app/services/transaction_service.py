from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Transaction types that decrease balance
_DEBIT_TYPES = {TransactionType.subtract, TransactionType.penalty, TransactionType.spend}


class TransactionService:
    """Core financial logic — every balance change goes through here."""

    @staticmethod
    async def execute_transaction(
        session: AsyncSession,
        *,
        player_id: int,
        curator_id: int,
        txn_type: TransactionType,
        amount: Decimal,
        description: str | None,
        request_id: str,
    ) -> tuple[Transaction, Decimal]:
        """
        Execute a financial transaction atomically.

        Steps:
        1. Check for duplicate request_id (idempotency).
        2. Validate player and curator exist.
        3. Verify curator has permission (curator or admin role).
        4. Lock the balance row with SELECT FOR UPDATE.
        5. Compute new balance and reject if it would go negative on debits.
        6. Insert transaction record.
        7. Update balance.
        8. Return transaction + new balance (caller commits).
        """

        # 1. Idempotency — check duplicate request_id
        existing = await session.execute(
            select(Transaction).where(Transaction.request_id == request_id)
        )
        dup = existing.scalar_one_or_none()
        if dup is not None:
            logger.warning("Duplicate request_id=%s, returning existing transaction id=%s", request_id, dup.id)
            balance_row = await session.get(Balance, dup.player_id)
            return dup, balance_row.current_balance  # type: ignore[union-attr]

        # 2. Validate player
        player = await session.get(User, player_id)
        if player is None:
            raise ValueError(f"Player with id={player_id} does not exist")

        # 3. Validate curator and role
        curator = await session.get(User, curator_id)
        if curator is None:
            raise ValueError(f"Curator with id={curator_id} does not exist")
        if curator.role not in (UserRole.curator, UserRole.admin):
            raise PermissionError(f"User id={curator_id} does not have curator/admin privileges")

        # 4. Lock balance row (SELECT FOR UPDATE)
        result = await session.execute(
            select(Balance)
            .where(Balance.player_id == player_id)
            .with_for_update()
        )
        balance_row = result.scalar_one_or_none()
        if balance_row is None:
            # Auto-create balance if missing (should not happen with proper user creation)
            balance_row = Balance(player_id=player_id, current_balance=Decimal("0.00"))
            session.add(balance_row)
            await session.flush()
            # Re-lock
            result = await session.execute(
                select(Balance)
                .where(Balance.player_id == player_id)
                .with_for_update()
            )
            balance_row = result.scalar_one()

        # 5. Compute new balance
        if txn_type == TransactionType.add:
            new_balance = balance_row.current_balance + amount
        else:
            new_balance = balance_row.current_balance - amount
            if new_balance < Decimal("0.00"):
                raise ValueError(
                    f"Insufficient balance. Current: {balance_row.current_balance}, "
                    f"Requested debit: {amount}"
                )

        # 6. Insert transaction
        txn = Transaction(
            player_id=player_id,
            curator_id=curator_id,
            type=txn_type,
            amount=amount,
            description=description,
            request_id=request_id,
        )
        session.add(txn)

        # 7. Update balance
        balance_row.current_balance = new_balance
        balance_row.updated_at = datetime.now(timezone.utc)

        await session.flush()

        logger.info(
            "Transaction id=%s type=%s player=%s amount=%s new_balance=%s request_id=%s",
            txn.id, txn_type.value, player_id, amount, new_balance, request_id,
        )

        return txn, new_balance

    @staticmethod
    async def get_balance(session: AsyncSession, player_id: int) -> Balance | None:
        player = await session.get(User, player_id)
        if player is None:
            return None
        return await session.get(Balance, player_id)

    @staticmethod
    async def get_history(
        session: AsyncSession, player_id: int, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        player = await session.get(User, player_id)
        if player is None:
            raise ValueError(f"Player with id={player_id} does not exist")
        result = await session.execute(
            select(Transaction)
            .where(Transaction.player_id == player_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
