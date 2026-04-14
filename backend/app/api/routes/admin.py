from __future__ import annotations

import csv
import io
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.balance import Balance
from app.models.transaction import Transaction
from app.models.user import User, UserRole
from app.schemas.schemas import UserCreate, UserOut
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


@router.get("/users", response_model=List[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserOut]:
    users = await UserService.get_all(session)
    return [UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    existing = await UserService.get_by_telegram_id(session, payload.telegram_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="User with this telegram_id already exists")
    role = UserRole(payload.role.value)
    async with session.begin():
        user = await UserService.create_user(
            session,
            telegram_id=payload.telegram_id,
            username=payload.username,
            role=role,
        )
    return UserOut.model_validate(user)


@router.get("/users/by-telegram/{telegram_id}", response_model=UserOut)
async def get_user_by_telegram(
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    user = await UserService.get_by_telegram_id(session, telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.get("/users/by-username/{username}", response_model=UserOut)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    user = await UserService.get_by_username(session, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.post("/users/ensure", response_model=UserOut)
async def ensure_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    """Get-or-create a user. Used by the bot on /start or first interaction."""
    role = UserRole(payload.role.value)
    async with session.begin():
        user = await UserService.ensure_user(
            session,
            telegram_id=payload.telegram_id,
            username=payload.username,
            role=role,
        )
    return UserOut.model_validate(user)


@router.get("/export")
async def export_data(session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    """Export all users, balances, and transactions as CSV."""
    # Fetch all data
    users_result = await session.execute(select(User).order_by(User.id))
    users = users_result.scalars().all()

    balances_result = await session.execute(select(Balance))
    balances = {b.player_id: b.current_balance for b in balances_result.scalars().all()}

    txn_result = await session.execute(select(Transaction).order_by(Transaction.created_at.desc()))
    transactions = txn_result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Users section
    writer.writerow(["=== USERS ==="])
    writer.writerow(["id", "telegram_id", "username", "role", "balance", "created_at"])
    for u in users:
        bal = balances.get(u.id, "N/A")
        writer.writerow([u.id, u.telegram_id, u.username or "", u.role.value, str(bal), u.created_at.isoformat()])

    writer.writerow([])
    writer.writerow(["=== TRANSACTIONS ==="])
    writer.writerow(["id", "player_id", "curator_id", "type", "amount", "description", "request_id", "created_at"])
    for t in transactions:
        writer.writerow([
            t.id, t.player_id, t.curator_id, t.type.value,
            str(t.amount), t.description or "", t.request_id, t.created_at.isoformat(),
        ])

    output.seek(0)
    logger.info("Export generated: %d users, %d transactions", len(users), len(transactions))
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )
