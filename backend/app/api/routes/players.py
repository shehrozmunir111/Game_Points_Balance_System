from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.schemas import BalanceOut, TransactionOut
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}/balance", response_model=BalanceOut)
async def get_balance(
    player_id: int,
    session: AsyncSession = Depends(get_session),
) -> BalanceOut:
    balance = await TransactionService.get_balance(session, player_id)
    if balance is None:
        raise HTTPException(status_code=404, detail=f"Player with id={player_id} not found")
    return BalanceOut.model_validate(balance)


@router.get("/{player_id}/history", response_model=List[TransactionOut])
async def get_history(
    player_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[TransactionOut]:
    try:
        transactions = await TransactionService.get_history(session, player_id, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [TransactionOut.model_validate(t) for t in transactions]
