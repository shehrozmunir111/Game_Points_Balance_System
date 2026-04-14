from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.transaction import TransactionType
from app.schemas.schemas import (
    TransactionOut,
    TransactionRequest,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _handle_transaction(
    txn_type: TransactionType,
    payload: TransactionRequest,
    session: AsyncSession,
) -> TransactionResponse:
    """Shared handler for all transaction types."""
    try:
        async with session.begin():
            txn, new_balance = await TransactionService.execute_transaction(
                session,
                player_id=payload.player_id,
                curator_id=payload.curator_id,
                txn_type=txn_type,
                amount=payload.amount,
                description=payload.description,
                request_id=payload.request_id,
            )
            txn_out = TransactionOut.model_validate(txn)
        return TransactionResponse(transaction=txn_out, new_balance=new_balance)
    except ValueError as exc:
        logger.warning("Transaction rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        logger.warning("Permission denied: %s", exc)
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error during %s transaction", txn_type.value)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/add", response_model=TransactionResponse)
async def add_points(
    payload: TransactionRequest,
    session: AsyncSession = Depends(get_session),
) -> TransactionResponse:
    return await _handle_transaction(TransactionType.add, payload, session)


@router.post("/subtract", response_model=TransactionResponse)
async def subtract_points(
    payload: TransactionRequest,
    session: AsyncSession = Depends(get_session),
) -> TransactionResponse:
    return await _handle_transaction(TransactionType.subtract, payload, session)


@router.post("/penalty", response_model=TransactionResponse)
async def penalty_points(
    payload: TransactionRequest,
    session: AsyncSession = Depends(get_session),
) -> TransactionResponse:
    return await _handle_transaction(TransactionType.penalty, payload, session)


@router.post("/spend", response_model=TransactionResponse)
async def spend_points(
    payload: TransactionRequest,
    session: AsyncSession = Depends(get_session),
) -> TransactionResponse:
    return await _handle_transaction(TransactionType.spend, payload, session)
