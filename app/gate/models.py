import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LeadMagnetRun(Base):
    """Tracks run counts per email + tool for rate limiting."""

    __tablename__ = "lead_magnet_run"
    __table_args__ = (
        UniqueConstraint("email_hash", "tool_slug", "run_period", name="uq_run_per_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    # YYYY-MM for monthly tools, "lifetime" for sales_business_plan
    run_period: Mapped[str] = mapped_column(String(10), nullable=False)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class LeadMagnetResult(Base):
    """Stores agent output for result permalink sharing (30-day TTL)."""

    __tablename__ = "lead_magnet_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True
    )
    tool_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
