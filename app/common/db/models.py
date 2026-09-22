from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db.base import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    message: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )