import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.gate.service import MONTHLY_LIMIT, check_rate_limit, hash_email, increment_run, run_period


class TestHashEmail:
    def test_deterministic(self) -> None:
        assert hash_email("user@example.com") == hash_email("user@example.com")

    def test_lowercase(self) -> None:
        assert hash_email("USER@EXAMPLE.COM") == hash_email("user@example.com")

    def test_strips_whitespace(self) -> None:
        assert hash_email("  user@example.com  ") == hash_email("user@example.com")

    def test_sha256_hex(self) -> None:
        h = hash_email("user@example.com")
        assert h == hashlib.sha256(b"user@example.com").hexdigest()
        assert len(h) == 64


class TestRunPeriod:
    def test_monthly_format(self) -> None:
        period = run_period("company_list")
        assert len(period) == 7
        assert period[4] == "-"

    def test_lifetime_for_sales_plan(self) -> None:
        assert run_period("sales_business_plan") == "lifetime"

    def test_monthly_for_meeting_prep(self) -> None:
        assert run_period("meeting_prep") != "lifetime"


class TestRateLimit:
    async def test_fresh_email_is_allowed(self, db: AsyncSession) -> None:
        allowed, count = await check_rate_limit(db, "fresh@example.com", "company_list")
        assert allowed is True
        assert count == 0

    async def test_allowed_below_limit(self, db: AsyncSession) -> None:
        for _ in range(MONTHLY_LIMIT - 1):
            await increment_run(db, "user@example.com", "company_list")
        allowed, count = await check_rate_limit(db, "user@example.com", "company_list")
        assert allowed is True
        assert count == MONTHLY_LIMIT - 1

    async def test_blocked_at_limit(self, db: AsyncSession) -> None:
        for _ in range(MONTHLY_LIMIT):
            await increment_run(db, "limit@example.com", "company_list")
        allowed, count = await check_rate_limit(db, "limit@example.com", "company_list")
        assert allowed is False
        assert count == MONTHLY_LIMIT

    async def test_different_tools_are_independent(self, db: AsyncSession) -> None:
        for _ in range(MONTHLY_LIMIT):
            await increment_run(db, "multi@example.com", "company_list")
        allowed, _ = await check_rate_limit(db, "multi@example.com", "meeting_prep")
        assert allowed is True

    async def test_increment_is_idempotent_upsert(self, db: AsyncSession) -> None:
        await increment_run(db, "upsert@example.com", "company_list")
        await increment_run(db, "upsert@example.com", "company_list")
        _, count = await check_rate_limit(db, "upsert@example.com", "company_list")
        assert count == 2
