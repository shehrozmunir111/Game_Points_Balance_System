from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserRoleEnum(str, Enum):
    player = "player"
    curator = "curator"
    admin = "admin"


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    role: UserRoleEnum = UserRoleEnum.player


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    role: UserRoleEnum
    created_at: datetime


# ── Balance Schemas ───────────────────────────────────────────────────────────

class BalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    current_balance: Decimal
    updated_at: datetime


# ── Transaction Schemas ───────────────────────────────────────────────────────

class TransactionTypeEnum(str, Enum):
    add = "add"
    subtract = "subtract"
    penalty = "penalty"
    spend = "spend"


class TransactionRequest(BaseModel):
    player_id: int
    curator_id: int
    amount: Decimal = Field(gt=0, description="Must be greater than 0")
    description: str | None = None
    request_id: str = Field(min_length=1, max_length=255)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    curator_id: int
    type: TransactionTypeEnum
    amount: Decimal
    description: str | None
    request_id: str
    created_at: datetime


class TransactionResponse(BaseModel):
    transaction: TransactionOut
    new_balance: Decimal


# ── Generic ───────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
