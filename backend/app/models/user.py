from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    player = "player"
    curator = "curator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.player)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    balance: Mapped["Balance"] = relationship("Balance", back_populates="player", uselist=False)
    transactions_as_player: Mapped[list["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.player_id", back_populates="player"
    )
    transactions_as_curator: Mapped[list["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.curator_id", back_populates="curator"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} role={self.role.value}>"
