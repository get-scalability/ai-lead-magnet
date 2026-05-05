import hashlib
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.settings import settings
from app.gate.models import LeadMagnetRun


logger = structlog.get_logger()

MONTHLY_LIMIT = 3
LIFETIME_TOOLS = {"sales_business_plan"}


def hash_email(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()


def run_period(tool_slug: str) -> str:
    return "lifetime" if tool_slug in LIFETIME_TOOLS else datetime.now(UTC).strftime("%Y-%m")


async def check_rate_limit(db: AsyncSession, email: str, tool_slug: str) -> tuple[bool, int]:
    """Return (is_allowed, runs_used_this_period)."""
    result = await db.execute(
        select(LeadMagnetRun).where(
            LeadMagnetRun.email_hash == hash_email(email),
            LeadMagnetRun.tool_slug == tool_slug,
            LeadMagnetRun.run_period == run_period(tool_slug),
        )
    )
    row = result.scalar_one_or_none()
    count = row.run_count if row else 0
    return count < MONTHLY_LIMIT, count


async def increment_run(db: AsyncSession, email: str, tool_slug: str) -> None:
    stmt = (
        insert(LeadMagnetRun)
        .values(
            email_hash=hash_email(email),
            tool_slug=tool_slug,
            run_period=run_period(tool_slug),
            run_count=1,
        )
        .on_conflict_do_update(
            constraint="uq_run_per_period",
            set_={"run_count": LeadMagnetRun.run_count + 1},
        )
    )
    await db.execute(stmt)
    await db.commit()


async def push_to_crm(payload: dict) -> None:
    """Fire-and-forget CRM push. Never raises — failures are logged only."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.SCALA_CRM_API_URL}leads",
                json=payload,
                headers={"Authorization": f"Bearer {settings.SCALA_APP_API_KEY.get_secret_value()}"},
            )
    except Exception:
        logger.warning("crm_push_failed", tool=payload.get("tool_used"))
