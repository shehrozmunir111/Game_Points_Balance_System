from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Balance(Base):
    __tablename__ = "balances"

    player_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=Decimal("0.00")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    player: Mapped["User"] = relationship("User", back_populates="balance")

    def __repr__(self) -> str:
        return f"<Balance player_id={self.player_id} balance={self.current_balance}>"
